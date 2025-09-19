###################################################################################
# ocr_translate - a django app to perform OCR and translation of images.          #
# Copyright (C) 2023-present Davide Grassano                                      #
#                                                                                 #
# This program is free software: you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by            #
# the Free Software Foundation, either version 3 of the License.                  #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program.  If not, see {http://www.gnu.org/licenses/}.           #
#                                                                                 #
# Home: https://github.com/Crivella/ocr_translate                                 #
###################################################################################
"""Django models for the ocr_translate app."""
import logging
from importlib.metadata import entry_points
from typing import Type

from django.db import models

from ..ocr_tsl.signals import refresh_model_cache_signal

logger = logging.getLogger('ocr.general')

def safe_get_or_create(model: Type[models.Model], strict: bool = False, **kwargs) -> models.Model:
    """Get or create a model instance in a safe way.

    Args:
        model (Type[models.Model]): The model class to get or create.
        strict (bool, optional): Whether to raise a caught exception if ocurred. Defaults to False.
    """
    try:
        obj, _ = model.objects.get_or_create(**kwargs)
    except model.MultipleObjectsReturned as exc:
        if strict:
            raise exc
        logger.warning(f'Multiple objects returned for {model}: {model.objects.filter(**kwargs).all()}')
        obj = model.objects.filter(**kwargs).first()
    return obj

class OptionDict(models.Model):
    """Dictionary of options for OCR and translation"""
    options = models.JSONField(unique=True)

    def __str__(self):
        return str(self.options)

class LoadEvent(models.Model):
    """Event log for the OCR and translation tasks"""
    description = models.CharField(max_length=512)

    date = models.DateTimeField(auto_now_add=True)

class Image(models.Model):
    """Image registered as the md5 of the uploaded file"""
    md5 = models.CharField(max_length=32, unique=True)


class Text(models.Model):
    """Text extracted from an image or translated from another text"""
    text = models.TextField()
    # lang = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='texts')

class Language(models.Model):
    """Language used for translation"""
    LOADED_MODEL_SRC: 'Language' = None
    LOADED_MODEL_DST: 'Language' = None

    name = models.CharField(max_length=64, unique=True)
    iso1 = models.CharField(max_length=8, unique=True)
    iso2b = models.CharField(max_length=8, unique=True)
    iso2t = models.CharField(max_length=8, unique=True)
    iso3 = models.CharField(max_length=32, unique=True)

    default_options = models.ForeignKey(
        OptionDict, on_delete=models.CASCADE, related_name='lang_default_options', null=True
        )

    load_events_src = models.ManyToManyField('LoadEvent', related_name='languages_src')
    load_events_dst = models.ManyToManyField('LoadEvent', related_name='languages_dst')

    def __str__(self):
        return f'{self.name} ({self.iso1})'

    def __eq__(self, other):
        if isinstance(other, Language):
            return self.iso1 == other.iso1
        if isinstance(other, str):
            return self.iso1 == other
        return False

    # https://stackoverflow.com/questions/61212514/django-model-objects-became-not-hashable-after-upgrading-to-django-2-2
    def __hash__(self):
        return hash(self.iso1)

    def load_src(self) -> None:
        """Load the language trie"""
        self.load_events_src.create(description=f'Loading SRC Language {self.name}')

    def load_dst(self) -> None:
        """Load the language trie"""
        self.load_events_dst.create(description=f'Loading DST Language {self.name}')

    @classmethod
    def from_dct(cls, data: dict) -> 'Language':
        """Create or update a language from a dictionary"""
        logger.debug(f'Creating/Updating Language from dict: {data}')

        data = data.copy()

        def_opt = data.pop('default_options', {})

        required = {'name', 'iso1', 'iso2t', 'iso2b', 'iso3'}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f'Missing required keys {missing} in data for Language')

        obj, _ = cls.objects.get_or_create(**data)
        opt_obj, created = OptionDict.objects.get_or_create(options=def_opt)
        if created:
            logger.debug(f'Created new OptionDict for Language {obj.name}: {def_opt}')
        obj.default_options = opt_obj
        obj.save()
        return obj

    @classmethod
    def get_last_loaded_src(cls) -> 'Language':
        """Get the last loaded language"""
        res = cls.objects
        # This is not a problem with SQLite, but with postgres, the order is not guaranteed when no date is set
        res = res.annotate(count=models.Count('load_events_src'))
        res = res.filter(count__gt=0)
        res = res.order_by('-load_events_src__date')
        res = res.first()
        if res is None or len(res.load_events_src.all()) == 0:
            logger.debug('No load events found for Language')
            return None
        return res

    @classmethod
    def get_last_loaded_dst(cls) -> 'Language':
        """Get the last loaded language"""
        res = cls.objects
        # This is not a problem with SQLite, but with postgres, the order is not guaranteed when no date is set
        res = res.annotate(count=models.Count('load_events_dst'))
        res = res.filter(count__gt=0)
        res = res.order_by('-load_events_dst__date')
        res = res.first()
        if res is None or len(res.load_events_dst.all()) == 0:
            logger.debug('No load events found for Language')
            return None
        return res

    @classmethod
    def load_model_src(cls, lang_iso1: str) -> 'Language':
        """Load a language by iso1 code and unload the current one if needed"""
        current = cls.LOADED_MODEL_SRC
        if current is not None:
            if current.iso1 == lang_iso1:
                return current

        logger.info(f'Loading Language SRC model: {lang_iso1}')
        obj = cls.objects.get(iso1=lang_iso1)
        obj.load_src()

        cls.LOADED_MODEL_SRC = obj
        refresh_model_cache_signal.send(sender=None)
        return obj

    @classmethod
    def load_model_dst(cls, lang_iso1: str) -> 'Language':
        """Load a language by iso1 code and unload the current one if needed"""
        current = cls.LOADED_MODEL_DST
        if current is not None:
            if current.iso1 == lang_iso1:
                return current

        logger.info(f'Loading Language DST model: {lang_iso1}')
        obj = cls.objects.get(iso1=lang_iso1)
        obj.load_dst()

        cls.LOADED_MODEL_DST = obj
        refresh_model_cache_signal.send(sender=None)
        return obj

    @classmethod
    def get_loaded_model_src(cls) -> 'Language':
        """Get the currently loaded source language"""
        return cls.LOADED_MODEL_SRC

    @classmethod
    def get_loaded_model_dst(cls) -> 'Language':
        """Get the currently loaded destination language"""
        return cls.LOADED_MODEL_DST

    @classmethod
    def unload_model_src(cls):
        """Unload the currently loaded source language if any"""
        current = cls.LOADED_MODEL_SRC
        if current is None:
            return
        logger.info(f'Unloading Language SRC model: {current.iso1}')
        cls.LOADED_MODEL_SRC = None
        refresh_model_cache_signal.send(sender=None)

    @classmethod
    def unload_model_dst(cls):
        """Unload the currently loaded destination language if any"""
        current = cls.LOADED_MODEL_DST
        if current is None:
            return
        logger.info(f'Unloading Language DST model: {current.iso1}')
        cls.LOADED_MODEL_DST = None
        refresh_model_cache_signal.send(sender=None)

class BaseModel(models.Model):
    """Mixin class for loading entrypoint models"""
    class Meta:
        abstract = True
    # This should be a dict of dicts where the key is the name of the option and the value contains:
    #  - type: The type of the option (str, int, float, bool)
    #  - default: The default value of the option (can be a callable that returns the default value)
    #  - description: A description of the option
    ALLOWED_OPTIONS = {}

    # Needed to run load tests on plugins without triggering load events
    DISABLE_LOAD_EVENTS = False

    # Map of key in model data to the related_name of the language field in the model
    CREATE_LANG_KEYS: dict[str, str] = {}

    LOADED_MODEL: 'BaseModel' = None

    entrypoint_namespace = None

    name = models.CharField(max_length=128)

    entrypoint = models.CharField(max_length=128, null=True)

    language_format = models.CharField(max_length=32, null=True)
    iso1_map = models.JSONField(null=True, blank=True)

    active = models.BooleanField(default=False)

    default_options = models.ForeignKey(
        OptionDict, on_delete=models.SET_NULL, related_name='used_by_%(class)s', null=True
        )

    load_events = models.ManyToManyField(LoadEvent, related_name='%(class)s')

    def __str__(self):
        return str(self.name)

    def __del__(self):
        try:
            self.unload()
        except NotImplementedError:
            pass

    def __getattribute__(self, name):
        res = super().__getattribute__(name)
        if name == 'DISABLE_LOAD_EVENTS':
            return res
        if not self.DISABLE_LOAD_EVENTS and name == 'load':
            def wrapped():
                _res = res()
                self.load_events.create(description=f'Loading model {self.name}')
                return _res
            return wrapped
        return res

    @classmethod
    def get_last_loaded(cls) -> 'BaseModel':
        """Get the last loaded model"""
        res = cls.objects
        res = res.filter(active=True)
        # This is not a problem with SQLite, but with postgres, the order is not guaranteed when no date is set
        res = res.annotate(count=models.Count('load_events'))
        res = res.filter(count__gt=0)
        res = res.order_by('-load_events__date')
        res = res.first()
        if res is None or len(res.load_events.all()) == 0:
            logger.debug(f'No load events found for {cls.__name__}')
            return None
        return res

    def get_lang_code(self, lang: 'Language') -> str:
        """Get the language code for a specific model"""
        if isinstance(self.iso1_map, dict) and lang.iso1 in self.iso1_map:
            return self.iso1_map[lang.iso1]
        return getattr(lang, self.language_format or 'iso1')

    @classmethod
    def from_dct(cls, _data: dict) -> 'BaseModel':
        """Create or update a model from a dictionary"""
        logger.debug(f'Creating/Updating {cls.__name__} from dict: {_data}')

        data = _data.copy()  # Avoid modifying the input dictionary
        def_opt = data.pop('default_options', {})

        if 'lang_code' in data:
            lang_code = data.pop('lang_code')
            if 'language_format' in data:
                logger.warning(f"Ignoring 'lang_code' in favor of 'language_format' for {data}")
            else:
                data['language_format'] = lang_code

        name = data.pop('name')
        langs = {}
        for key in cls.CREATE_LANG_KEYS:
            try:
                langs[key] = data.pop(key)
            except KeyError as exc:
                raise KeyError(f'Missing key {key} in data for {cls.__name__} {name}={data}') from exc
            if not isinstance(langs[key], (list, tuple)):
                raise TypeError(f'Key {key} must be a list or tuple in data for {cls.__name__}')

        data.setdefault('active', True)
        obj, _ = cls.objects.update_or_create(
            name=name,
            defaults=data,
        )

        for key, lang_list in langs.items():
            lang_objs = Language.objects.filter(iso1__in=lang_list).all()

            invalid = set(lang_list) - set(l.iso1 for l in lang_objs)
            if invalid:
                raise ValueError(f'Invalid languages {invalid} for {cls.__name__} <- {data}')

            model_key = cls.CREATE_LANG_KEYS[key]

            related: models.ManyToManyField[Language] = getattr(obj, model_key)

            new = set(lang_objs)
            prv = set(related.all())

            to_add = new - prv
            to_rmv = prv - new

            if to_rmv:
                related.remove(*to_rmv)
            if to_add:
                related.add(*to_add)

            if to_add or to_rmv:
                logger.debug(f'Updating {model_key} for OCRModel {name}:')
                to_add = [l.iso1 for l in to_add]
                to_rmv = [l.iso1 for l in to_rmv]
                logger.debug(f'  + {to_add}')
                logger.debug(f'  - {to_rmv}')

        opt_obj, created = OptionDict.objects.get_or_create(options=def_opt)
        if created:
            logger.debug(f'Created new OptionDict for {cls.__name__} {name}: {def_opt}')
        obj.default_options = opt_obj
        obj.save()

        return obj

    @classmethod
    def from_entrypoint(cls, name: str) -> 'BaseModel':
        """Get the entrypoint specific TSL model class from the entrypoint name"""
        if cls.entrypoint_namespace is None:
            raise ValueError('Cannot load base model class from entrypoint.')

        obj = cls.objects.get(name=name)
        ept = obj.entrypoint

        logger.debug(f'Loading model {name} from entrypoint {cls.entrypoint_namespace}:{ept}')
        for entrypoint in entry_points(group=cls.entrypoint_namespace, name=ept):
            new_cls = entrypoint.load()
            break
        else:
            raise ValueError(f'Missing plugin: Entrypoint "{ept}" not found.')

        return new_cls.objects.get(name=name)

    def load(self) -> None:
        """Placeholder method for loading the model. To be implemented via entrypoint"""
        raise NotImplementedError('The base model class does not implement this method.')

    def unload(self) -> None:
        """Placeholder method for unloading the model. To be implemented via entrypoint"""
        raise NotImplementedError('The base model class does not implement this method.')

    @classmethod
    def load_model(cls, model_name: str) -> 'BaseModel':
        """Load a model by name and unload the current one if needed"""
        current = cls.get_loaded_model()
        if current is not None:
            if current.name == model_name:
                return current
            current.unload()

        logger.info(f'Loading {cls.__name__} model: {model_name}')
        obj = cls.from_entrypoint(model_name)
        obj.load()

        cls.LOADED_MODEL = obj
        return obj

    @classmethod
    def unload_model(cls):
        """Unload the currently loaded model if it is this one"""
        current = cls.get_loaded_model()
        if current is None:
            return
        logger.info(f'Unloading {cls.__name__} model: {current.name}')
        current.unload()
        cls.LOADED_MODEL = None

    @classmethod
    def get_loaded_model(cls) -> 'BaseModel':
        """Get the currently loaded model"""
        return cls.LOADED_MODEL

    def deactivate(self):
        """Deactivate the model and unload it if it is currently loaded"""
        cls = self.__class__

        current = cls.get_loaded_model()
        if self.active:
            self.active = False
            self.save()
        if current is not None and current.name == self.name:
            cls.unload_model()

    def activate(self):
        """Activate the model"""
        if not self.active:
            self.active = True
            self.save()

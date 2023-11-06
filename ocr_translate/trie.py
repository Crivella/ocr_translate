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
"""Trie data structure implementation."""

class TrieNode:
    """Node of the Trie data structure."""
    def __init__(self):
        self.children = {}
        self.is_word = False
        self.freq = 0.0

    def __str__(self) -> str:
        return f'TrieNode(childs: {list(self.children.keys())}, is_word: {self.is_word})'

    def __contains__(self, key: str) -> bool:
        return key in self.children

    def __getitem__(self, key: str) -> 'TrieNode':
        return self.children.get(key, None)

    def __setitem__(self, key: str, value: 'TrieNode') -> None:
        self.children[key] = value

class Trie:
    """Trie data structure."""
    def __init__(self):
        self.root = TrieNode()
        self.charset = set()

    def insert(self, word: str, freq: float = 0.0) -> None:
        """Insert a word in the Trie."""
        self.charset.update(word)

        node = self.root

        for char in word:
            node = node.children.setdefault(char, TrieNode())

        node.is_word = True
        node.freq = freq

    def search(self, word: str, strict: bool = False, node = None) -> bool:
        """Search a word in the Trie.

        Args:
            word (str): Word to search.
            strict (bool, optional): If True, return False if the word contains characters not in the Trie.
                If False, ignore characters not in the Trie.
                Defaults to False.
            node (TrieNode, optional): Current node in the recursion. Defaults to None.

        Returns:
            bool: True if the word is in the Trie, False otherwise.
        """
        if node is None:
            node = self.root

        for char in word:
            if char not in self.charset:
                if strict:
                    return False
                continue
            if char not in node.children:
                return False

            node = node.children[char]

        if node is self.root and not strict:
            return True

        return node.is_word

    def get_freq(self, word: str) -> float:
        """Return the frequency of a word in the Trie.

        Args:
            word (str): Word to search.

        Returns:
            float: Frequency of the word in the Trie.
        """
        node = self.root

        for char in word:
            if char not in node.children:
                return 0.0

            node = node.children[char]

        if not node.is_word:
            return 0.0

        return node.freq

    def autocomplete(self, prefix: str) -> list[str]:
        """Autocomplete a prefix.

        Args:
            prefix (str): Prefix to autocomplete.

        Returns:
            list[str]: List of words that start with the prefix.
        """
        node = self.root

        for char in prefix:
            if char not in node.children:
                return []

            node = node.children[char]

        res = self._autocomplete(node, prefix)

        res.sort(key=self.get_freq, reverse=True)

        return res

    def _autocomplete(self, node: TrieNode, prefix: str) -> list[str]:
        """Internal function to autocomplete a prefix.

        Args:
            node (TrieNode): Current node in the recursion.
            prefix (str): Current prefix in the recursion.

        Returns:
            list[str]: List of words that start with the prefix.
        """
        results = []

        if node.is_word:
            results.append(prefix)

        for char, child in node.children.items():
            results.extend(self._autocomplete(child, prefix + char))

        return results

    def decompose(self, word: str, min_length: int = 3) -> list[list[str]]:
        """Fing all combinations of existing words that make up the given word.
        E.G: "thisissparta" (min_length=2) -> [['this', 'is', 'spar', 'ta'], ['this', 'is', 'sparta']]

        Args:
            word (str): Word to decompose.
            min_length (int, optional): Minimum length of the words to be decomposed into. Defaults to 3.

        Returns:
            list[list[str]]: list of all possible decompositions, where a decomposition is a list of words.
        """
        if len(word) < min_length:
            return [[word]]

        res = self._decompose(word, min_length)

        app = Trie()
        app.root = res

        return app.get_all_branches()

    def _decompose(self, word: str, min_length: int = 3) -> TrieNode:
        """Recursive implementation of decompose()."""
        node = TrieNode()
        res = node
        length = len(word)

        for i in range(min_length, length+1):
            if self.search(word[:i]):
                if i == length:
                    node.children.setdefault(word[:i], TrieNode())
                    new = TrieNode()
                    new.is_word = True
                    node.children[word[:i]] = new
                else:
                    node.children[word[:i]] = self._decompose(word[i:], min_length)

        return res

    def get_all_substitutions(self, word: str, max_num: int = 1) -> list[str]:
        """Get all possible substitutions of a word.

        Args:
            word (str): Word to substitute.
            max_num (int, optional): Maximum number of substitutions. Defaults to 2.

        Returns:
            list[str]: List of all possible substitutions.
        """
        if max_num > len(word):
            max_num = len(word)

        res = self._get_all_substitutions(word, max_num)
        res = list(set(res))
        if word in res:
            res.remove(word)

        res.sort(key=self.get_freq, reverse=True)

        return res

    def _get_all_substitutions(self, word: str, max_num: int = 1, invalid_ok: bool = False) -> list[str]:
        """Recursive implementation of get_all_substitutions()."""
        results = []

        if max_num == 0:
            return results

        ptr = self.root
        for i,char_in in enumerate(word):
            for char, node in ptr.children.items():
                if char == char_in:
                    continue
                new = word[:i] + char + word[i+1:]
                if invalid_ok or self.search(word[i+1:], strict=True, node=node):
                    results.append(new)
                # Not in if: Possible 1 sub is not a valid word but 2 or more subs are
                # appa -> apna -> anna (if appa and anna are words but apna is not)
                results.extend(self._get_all_substitutions(new, max_num-1, invalid_ok=invalid_ok))
            ptr  = ptr[char_in]
            if ptr is None:
                break

        return results

    def get_all_deletions(self, word: str, max_num: int = 1) -> list[str]:
        """Get all possible deletions of a word.

        Args:
            word (str): Word to delete.
            max_num (int, optional): Maximum number of deletions. Defaults to 2.

        Returns:
            list[str]: List of all possible deletions.
        """
        if max_num > len(word):
            max_num = len(word)

        res = self._get_all_deletions(word, max_num)
        res = list(set(res))

        res.sort(key=self.get_freq, reverse=True)

        return res

    def _get_all_deletions(self, word: str, max_num: int = 1) -> list[str]:
        """Recursive implementation of get_all_deletions()."""
        results = []

        if max_num == 0:
            return results

        for i in range(len(word)):
            new = word[:i] + word[i+1:]
            if self.search(new, strict=True):
                results.append(new)
            results.extend(self._get_all_deletions(new, max_num-1))

        return results

    def get_all_insertions(self, word: str, max_num: int = 1) -> list[str]:
        """Get all possible insertions of a word.

        Args:
            word (str): Word to insert.
            max_num (int, optional): Maximum number of insertions. Defaults to 2.

        Returns:
            list[str]: List of all possible insertions.
        """
        res = self._get_all_insertions(word, max_num)
        res = list(set(res))

        res.sort(key=self.get_freq, reverse=True)

        return res

    def _get_all_insertions(self, word: str, max_num: int = 1) -> list[str]:
        """Recursive implementation of get_all_insertions()."""
        results = []

        if max_num == 0:
            return results

        for i in range(len(word)+1):
            for char in self.charset:
                new = word[:i] + char + word[i:]
                if self.search(new, strict=True):
                    results.append(new)
                results.extend(self._get_all_insertions(new, max_num-1))

        return results

    def autocorrect_bayes(self, word: str, max_num: int = 1, distance_exp_factor: float = 2) -> list[str]:
        """Autocorrect a word bases on its probability.

        Args:
            word (str): Word to autocorrect.
            max_num (int, optional): Maximum number of autocorrections. Defaults to 2.
            distance_exp_factor (float, optional): Exponential (dist+1)^N factor for the distance of the autocorrection.

        Returns:
            list[str]: List of all possible autocorrections.
        """
        possible = []
        if self.search(word):
            possible.append((word, self.get_freq(word)))

        possible.extend(self._autocorrect_bayes(word, max_num, distance_exp_factor))

        possible.sort(key=lambda x: x[1], reverse=True)

        res = []
        for poss in possible:
            if poss[0] not in res:
                res.append(poss[0])

        return res

    def _autocorrect_bayes(self, word: str, max_num: int = 1, distance_exp_factor: float = 2) -> list[str]:
        """Recursive implementation of autocorrect_bayes()."""
        results = []

        if max_num == 0:
            return results

        # Also add all possible combinations of substitutions + deletion/insertion
        for i in range(1, max_num):
            for sub in  self._get_all_substitutions(word, i, invalid_ok=True):
                print(f'{sub = }')
                results.extend(self._get_all_deletions(sub, max_num-i))
                results.extend(self._get_all_insertions(sub, max_num-i))

        results.extend(self._get_all_substitutions(word, max_num))
        results.extend(self._get_all_deletions(word, max_num))
        results.extend(self._get_all_insertions(word, max_num))

        results = [(res, self.get_freq(res) / (max_num+1)**distance_exp_factor) for res in results]

        results.extend(self._autocorrect_bayes(word, max_num-1, distance_exp_factor))

        return results

    def get_all_branches(self) -> list[list[str]]:
        """Return a list of all valid (terminating in a word) branches of the Trie.

        Returns:
            list[list[str]]: List of all branches where a branch is a list of values of TrieNodes up to a valid word.
        """
        return self._get_all_branches(self.root)

    def _get_all_branches(self, node: TrieNode) -> list[list[str]]:
        """Recursive implementation of get_all_branches()."""
        results = []

        for elem, child in node.children.items():
            if child.is_word:
                results.append([elem])
            recurs = self._get_all_branches(child)
            for res in recurs:
                results.append([elem] + res)

        return results

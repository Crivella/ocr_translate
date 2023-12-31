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
"""Tests for trie data structure."""

from ocr_translate.trie import Trie, TrieNode


def test_node_init():
    """Test TrieNode.__init__ method."""
    node = TrieNode()
    assert isinstance(node.children, dict) and len(node.children) == 0
    assert node.is_word is False
    assert node.freq == 0.0

def test_node_str():
    """Test TrieNode.__str__ method."""
    node = TrieNode()
    assert str(node) == 'TrieNode(childs: [], is_word: False)'

def test_node_getitem():
    """Test TrieNode.__getitem__ method."""
    node = TrieNode()
    new = TrieNode()
    node.children['a'] = new
    new.children['b'] = TrieNode()
    assert node['a'] is node.children['a']
    assert node['a']['b'] is node.children['a'].children['b']
    assert node['b'] is None

def test_node_setitem():
    """Test TrieNode.__setitem__ method."""
    node = TrieNode()
    new = TrieNode()
    node['a'] = new
    new['b'] = TrieNode()
    assert node.children['a'] is new
    assert node.children['a'].children['b'] is new.children['b']

def test_node_contains():
    """Test TrieNode.__contains__ method."""
    node = TrieNode()
    new = TrieNode()
    node.children['a'] = new
    assert 'a' in node
    assert 'b' not in node

def test_trie_init():
    """Test Trie.__init__ method."""
    trie = Trie()
    assert isinstance(trie.root.children, dict) and len(trie.root.children) == 0
    assert trie.root.is_word is False
    assert trie.root.freq == 0.0
    assert trie.charset == set()

def test_trie_insert():
    """Test Trie.insert method."""
    trie = Trie()
    trie.insert('test')

    root = trie.root
    assert isinstance(root['t'], TrieNode)
    assert isinstance(root['t']['e'], TrieNode)
    assert isinstance(root['t']['e']['s'], TrieNode)
    assert isinstance(root['t']['e']['s']['t'], TrieNode)

    assert root['t']['e']['s']['t'].children == {}
    assert root['t']['e']['s']['t'].is_word is True

def test_trie_insert_freq():
    """Test Trie.insert method with freq."""
    trie = Trie()
    trie.insert('a', freq=0.5)

    child = trie.root.children['a']
    assert isinstance(child, TrieNode)
    assert child.freq == 0.5
    assert trie.get_freq('a') == 0.5

def test_trie_get_freq_in_trie():
    """Test Trie.get_freq method with a word in the Trie."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    assert trie.get_freq('test') == 0.5

def test_trie_get_freq_not_in_trie():
    """Test Trie.get_freq method with a word not in the Trie."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    assert trie.get_freq('testa') == 0.0

def test_trie_get_freq_incomplete():
    """Test Trie.get_freq method with an incomplete word."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    assert trie.get_freq('tes') == 0.0

def test_trie_insert_charset():
    """Test Trie.insert method with charset."""
    trie = Trie()
    trie.insert('test')
    assert trie.charset == {'t', 'e', 's'}

def test_trie_search():
    """Test Trie.search method."""
    trie = Trie()
    trie.insert('test')
    assert trie.search('test') is True

def test_trie_search_in_trie_nostrict():
    """Test Trie.search method with a word in the Trie + extra chars not in trie without strict."""
    trie = Trie()
    trie.insert('test')
    assert trie.search('testa') is True

def test_trie_search_not_in_trie_strict():
    """Test Trie.search method with a word in the Trie + extra chars not in trie with strict."""
    trie = Trie()
    trie.insert('test')
    assert trie.search('testa', strict=True) is False

def test_trie_search_zero_len_nostrict():
    """Test Trie.search method with a zero length word without strict."""
    trie = Trie()
    trie.insert('test')
    assert trie.search('') is True

def test_trie_search_zero_len_strict():
    """Test Trie.search method with a zero length word with strict."""
    trie = Trie()
    trie.insert('test')
    assert trie.search('', strict=True) is False

def test_trie_autocomplete_correct_sort():
    """Test Trie.autocomplete method with correct sorting."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    trie.insert('testa', freq=0.3)
    trie.insert('testb', freq=0.7)
    trie.insert('testc', freq=0.1)

    res = trie.autocomplete('test')
    assert res == ['testb', 'test', 'testa', 'testc']

def test_trie_autocomplete_correct_sort_incomplete():
    """Test Trie.autocomplete method with correct sorting and incomplete prefix."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    trie.insert('testa', freq=0.3)
    trie.insert('testb', freq=0.7)
    trie.insert('testc', freq=0.1)

    res = trie.autocomplete('tes')
    assert res == ['testb', 'test', 'testa', 'testc']

def test_trie_autocomplete_unkown_prefix():
    """Test Trie.autocomplete method with unknown prefix."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    trie.insert('testa', freq=0.3)
    trie.insert('testb', freq=0.7)
    trie.insert('testc', freq=0.1)

    res = trie.autocomplete('tesa')
    assert isinstance(res, list) and len(res) == 0

def test_trie_decompose_lessthanmin():
    """Test Trie.decompose method with less than min_len."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    trie.insert('testa', freq=0.3)
    trie.insert('testb', freq=0.7)
    trie.insert('testc', freq=0.1)

    res = trie.decompose('tes', min_length=4)
    assert res == [['tes']]

def test_trie_decompose_known_word():
    """Test Trie.decompose method with one known word."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    trie.insert('testa', freq=0.3)
    trie.insert('testb', freq=0.7)
    trie.insert('testc', freq=0.1)

    res = trie.decompose('test', min_length=3)
    assert res == [['test']]

def test_trie_decompose():
    """Test Trie.decompose method with one known word."""
    trie = Trie()
    trie.insert('test', freq=0.5)
    trie.insert('testtest', freq=0.3)

    res = trie.decompose('testtest', min_length=3)
    assert res == [['test', 'test'], ['testtest']]

def test_trie_get_all_branches():
    """Test Trie.get_all_branches method."""
    trie = Trie()
    trie.insert('a')
    trie.insert('aa')
    trie.insert('aab')
    trie.insert('aac')

    res = trie.get_all_branches()
    assert res == [['a'], ['a', 'a'], ['a', 'a', 'b'], ['a', 'a', 'c']]

def test_trie_get_all_branches_with_invalid_termination():
    """Test Trie.get_all_branches method with invalid termination."""
    trie = Trie()
    trie.insert('a')
    trie.insert('aa')
    trie.insert('aab')
    trie.insert('aac')

    trie.root['a']['b'] = TrieNode()

    res = trie.get_all_branches()
    assert res == [['a'], ['a', 'a'], ['a', 'a', 'b'], ['a', 'a', 'c']]

def test_trie_get_all_substitutions_max1():
    """Test Trie.get_all_substitutions method with maximum 1 substitution."""
    trie = Trie()
    trie.insert('a')
    trie.insert('aa')
    trie.insert('b')
    trie.insert('c')

    res = trie.get_all_substitutions('a', max_num=1)
    assert sorted(res) == sorted(['b', 'c'])

def test_trie_get_all_substitutions_max2():
    """Test Trie.get_all_substitutions method with maximum 2 substitutions."""
    trie = Trie()
    trie.insert('a')
    trie.insert('aa')
    trie.insert('ab')
    trie.insert('bb')
    trie.insert('cc')
    trie.insert('c')

    res = trie.get_all_substitutions('aa', max_num=2)
    assert sorted(res) == sorted(['ab', 'bb', 'cc'])

def test_trie_get_all_substitutions_max_gt_len():
    """Test Trie.get_all_substitutions method with maximum 1 substitution."""
    trie = Trie()
    trie.insert('a')
    trie.insert('aa')
    trie.insert('b')
    trie.insert('c')

    res = trie.get_all_substitutions('a', max_num=2)
    assert sorted(res) == sorted(['b', 'c'])

def test_trie_get_all_deletions_max1():
    """Test Trie.get_all_deletions method with maximum 1 deletion."""
    trie = Trie()
    trie.insert('a')
    trie.insert('ab')
    trie.insert('b')
    trie.insert('c')

    res = trie.get_all_deletions('ab', max_num=1)
    assert sorted(res) == sorted(['a', 'b'])

def test_trie_get_all_deletions_max2():
    """Test Trie.get_all_deletions method with maximum 2 deletions."""
    trie = Trie()
    trie.insert('a')
    trie.insert('ab')
    trie.insert('aa')
    trie.insert('abc')
    trie.insert('bc')
    trie.insert('ac')
    trie.insert('c')
    trie.insert('d')

    res = trie.get_all_deletions('abc', max_num=2)
    assert sorted(res) == sorted(['a', 'ab', 'ac', 'bc', 'c'])

def test_trie_get_all_deletions_max_gt_len():
    """Test Trie.get_all_deletions method with maximum 1 deletion."""
    trie = Trie()
    trie.insert('a')
    trie.insert('ab')
    trie.insert('b')
    trie.insert('c')

    res = trie.get_all_deletions('ab', max_num=3)
    assert sorted(res) == sorted(['a', 'b'])

def test_trie_get_all_insertions_max1():
    """Test Trie.get_all_insertions method with maximum 1 insertion."""
    trie = Trie()
    trie.insert('a')
    trie.insert('ab')
    trie.insert('ad')
    trie.insert('b')

    res = trie.get_all_insertions('a', max_num=1)
    assert sorted(res) == sorted(['ab', 'ad'])

def test_trie_get_all_insertions_max2():
    """Test Trie.get_all_insertions method with maximum 2 insertions."""
    trie = Trie()
    trie.insert('a')
    trie.insert('ab')
    trie.insert('aa')
    trie.insert('abc')
    trie.insert('bc')
    trie.insert('ac')
    trie.insert('c')

    res = trie.get_all_insertions('a', max_num=2)
    assert sorted(res) == sorted(['ab', 'aa', 'abc', 'ac'])

def test_trie_autocorrect_bayes_max1():
    """Test Trie.autocorrect_bayes method."""
    trie = Trie()
    trie.insert('a')
    trie.insert('ab')
    trie.insert('aa')
    trie.insert('abc')
    trie.insert('abcd')
    trie.insert('abdd')
    trie.insert('bc')
    trie.insert('ac')
    trie.insert('c')
    trie.insert('d')

    res = trie.autocorrect_bayes('abc', max_num=1)
    assert sorted(res) == sorted(['ab', 'abc', 'abcd', 'ac', 'bc'])

def test_trie_autocorrect_bayes_max2():
    """Test Trie.autocorrect_bayes method."""
    trie = Trie()
    trie.insert('a')
    trie.insert('ab')
    trie.insert('aa')
    trie.insert('abc')
    trie.insert('abcd')
    trie.insert('abdd')
    trie.insert('bc')
    trie.insert('ac')
    trie.insert('c')
    trie.insert('d')

    res = trie.autocorrect_bayes('abc', max_num=2)
    assert sorted(res) == sorted(['a', 'c', 'aa', 'ab', 'abc', 'abcd', 'abdd', 'ac', 'bc'])

def test_trie_autocorrect_bayes_nofreq():
    """Test Trie.autocorrect_bayes method with no freq."""
    trie = Trie()
    trie.insert('ab')
    trie.insert('aa')

    res = trie.autocorrect_bayes('aa', max_num=1)
    assert res[0] == 'aa'

def test_trie_autocorrect_bayes_freq():
    """Test Trie.autocorrect_bayes method with freq."""
    trie = Trie()
    trie.insert('ab', 0.1)
    trie.insert('aa')

    res = trie.autocorrect_bayes('aa', max_num=1)
    assert res[0] == 'ab'

def test_trie_autocorrect_bayes_freq_favor1():
    """Test Trie.autocorrect_bayes method with freq."""
    trie = Trie()
    trie.insert('ab', 4)
    trie.insert('a', 9 - 0.1)

    res = trie.autocorrect_bayes('abc', max_num=2)
    assert res[0] == 'ab'

def test_trie_autocorrect_bayes_freq_favor2():
    """Test Trie.autocorrect_bayes method with freq."""
    trie = Trie()
    trie.insert('ab', 4)
    trie.insert('a', 9 + 0.1)

    res = trie.autocorrect_bayes('abc', max_num=2)
    assert res[0] == 'a'

def test_trie_autocorrect_bayes_freq_favor1_factor():
    """Test Trie.autocorrect_bayes method with freq."""
    trie = Trie()
    trie.insert('ab', 4)
    trie.insert('a', 9 + 0.1)

    res = trie.autocorrect_bayes('abc', max_num=2, distance_exp_factor=2.1)
    assert res[0] == 'ab'

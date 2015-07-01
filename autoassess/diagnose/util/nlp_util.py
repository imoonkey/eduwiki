__author__ = 'moonkey'

import nltk
import string
import os
import nltk.parse.stanford
import nltk_tgrep
import sys
import traceback
# TODO:: test loading the parsers and tokenizers globally, i.e., the following
# load the tokenizers and the parsers in the module, and then just use the global object in NlpUtil

from nltk.corpus import wordnet
import pattern.en


def load_punkt_tokenizer():
    # print >> sys.stderr, "loading tokenizer"
    return nltk.data.load('tokenizers/punkt/english.pickle')


def load_stanford_parser():
    # print >> sys.stderr, "loading stanford_parser"
    # os.environ['STANFORD_PARSER'] = os.path.join(
    # os.path.expanduser('~'), 'stanford-parser/stanford-parser.jar')
    # os.environ['STANFORD_MODELS'] = os.path.join(
    # os.path.expanduser('~'), 'stanford-parser/stanford-parser-3.5.2-models.jar')
    os.environ['STANFORD_PARSER'] = os.path.join(
        '/opt/stanford-parser/stanford-parser.jar')
    os.environ['STANFORD_MODELS'] = os.path.join(
        '/opt/stanford-parser/stanford-parser-3.5.2-models.jar')
    parser = nltk.parse.stanford.StanfordParser(
        model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
    return parser


PUNKT_TOKENIZER = load_punkt_tokenizer()
STANFORD_PARSER = load_stanford_parser()


class NlpUtil:
    def __init__(self):
        # print >> sys.stderr, "loading NlpUtil()"
        self.tokenizer = PUNKT_TOKENIZER
        self.parser = STANFORD_PARSER
        # self.tokenizer = None
        # self.parser = None

    def _load_tokenizer(self):
        try:
            if not self.tokenizer:
                self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
                return True
        except:
            raise Exception

    def _load_parser(self):
        if self.parser:
            # print >> sys.stderr, 'parser already there'
            return True
        try:
            os.environ['STANFORD_PARSER'] = os.path.join(
                '/opt/stanford-parser/stanford-parser.jar')
            os.environ['STANFORD_MODELS'] = os.path.join(
                '/opt/stanford-parser/stanford-parser-3.5.2-models.jar')
            self.parser = nltk.parse.stanford.StanfordParser(
                model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
            return True
        except Exception:
            raise Exception

    def punkt_tokenize(self, text):
        """
        NLTK sentence tokenizer
        http://www.nltk.org/_modules/nltk/tokenize/punkt.html
        The algorithm for this tokenizer is described in::
            Kiss, Tibor and Strunk, Jan (2006): Unsupervised Multilingual Sentence
            Boundary Detection.  Computational Linguistics 32: 485-525.
        :param text:
        :return:
        """
        if not self.tokenizer:
            self._load_tokenizer()
        sentences = self.tokenizer.tokenize(text)
        return sentences

    def parsing(self, text):
        if not self.parser:
            self._load_parser()
        tokens = nltk.word_tokenize(text)
        # print >> sys.stderr, tokens
        # tagged = nltk.pos_tag(tokens)
        try:
            parsed = self.parser.parse(tokens).next()
        except Exception, err:
            # print >> sys.stderr, "the sentence cannot be parsed"
            print >> sys.stderr, str(err)
            traceback.print_exc(file=sys.stderr)
            return None
        # print >> sys.stderr, "parsed_tree:" + str(parsed)
        return parsed

    @staticmethod
    def tgrep_positions(sent_tree, pattern):
        if type(sent_tree) is not nltk.tree.ParentedTree:
            sent_tree = nltk.tree.ParentedTree.convert(sent_tree)
        matched_positions = nltk_tgrep.tgrep_positions(sent_tree, pattern)

        # TODO:: insepct other functions, is there a result like in regex where each parts are separated?
        return matched_positions

    @classmethod
    def tgrep(cls, sent_tree, pattern):
        return sent_tree[cls.tgrep_positions(sent_tree, pattern)]

    @staticmethod
    def untokenize(tokens):
        sentence = "".join(
            [" " + i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()
        return sentence

    @staticmethod
    def revert_penntreebank_symbols(text):
        dic = {
            '-LRB- ': '(',
            ' -RRB-': ')',
            '-LSB- ': '[',
            ' -RSB-': ']'
        }
        for i, j in dic.iteritems():
            text = text.replace(i, j)
        return text

    @staticmethod
    def find_sentence_tenses(sentence_tree, vp_pos):
        verbal_tree = sentence_tree[vp_pos]

        verb_node = NlpUtil.find_verb_node_in_VP(verbal_tree=verbal_tree)
        tenses = None
        if verb_node and 'VB' in verb_node.label():
            sent_verb = verb_node[0]
            possible_tenses = pattern.en.tenses(sent_verb)
            # "was" can match both person 1 and 3
            if possible_tenses:
                tenses = max(possible_tenses)
                # 'PRESENT'>'PAST'; 'person': 3>2>1>'None';

        return tenses

    @staticmethod
    def match_sentence_tense(verbal_tree, target_tenses):
        # TODO:: what if there are multiple verbs, connected by "and"/"or" etc.
        if not target_tenses:
            return verbal_tree
        if type(verbal_tree) == nltk.tree.Tree:
            verbal_tree = nltk.tree.ParentedTree.convert(verbal_tree)
        verb_node = NlpUtil.find_verb_node_in_VP(verbal_tree=verbal_tree)
        if verb_node:
            original_verb = verb_node[0]
            conjugated_verb = pattern.en.conjugate(original_verb, target_tenses)
            if conjugated_verb != original_verb:
                verb_node[0] = conjugated_verb
                try:
                    original_tenses = max(pattern.en.tenses(original_verb))
                except Exception as e:
                    print e
                    return verbal_tree
                target_sp_form = target_tenses[2]
                original_sp_form = original_tenses[2]
                if target_sp_form != original_sp_form and 'be' == pattern.en.lemma(original_verb):
                    # find NPs in the same level
                    parent_vp = verb_node.parent()
                    if "VP" in parent_vp.label():
                        # skip the nodes before verb_node
                        verb_idx = len(parent_vp)
                        following_nps = []
                        for idx, child in enumerate(parent_vp):
                            if child == verb_node:
                                verb_idx = idx
                                continue
                            if idx < verb_idx:
                                continue
                            if "NP" in child.label():
                                following_nps.append(child)

                        # #####################################
                        def get_np_child(node):
                            if node is None or type(node) is str:
                                return None
                            for child in node:
                                if 'NP' or 'NN' in child.label():
                                    return child
                            return None

                        def has_nn_child(node):
                            if node is None or type(node) is str:
                                return False
                            for child in node:
                                if 'NN' in child.label():
                                    return True
                            return False

                        ######################################

                        for np in following_nps:
                            # TODO:: modify the singular/plural forms of noun phrases!
                            np_to_modify = np
                            while not has_nn_child(np_to_modify):
                                np_to_modify = get_np_child(np_to_modify)
                                if np_to_modify is None:
                                    break
                            if np_to_modify:
                                to_remove = []
                                for child in np_to_modify:
                                    if 'DT' == child.label() \
                                            and child[0] is not 'the' \
                                            and target_sp_form == 'plural':
                                        to_remove.append(child)
                                    if 'NN' in child.label():
                                        if target_sp_form == 'plural':
                                            child[0] = pattern.en.pluralize(child[0])
                                        else:
                                            child[0] = pattern.en.singularize(child[0])
                                for t in to_remove:
                                    np_to_modify.remove(t)

        return verbal_tree

    @staticmethod
    def find_verb_node_in_VP(verbal_tree, priority='verb'):
        """
        @return: the VB or the MD, whichever to be morphed
        """

        if type(verbal_tree) is str:
            return None
        verb_node = verbal_tree

        while type(verb_node[0]) is not str and 'VP' in verb_node.label():
            # TODO:: this while loop is basically nonsense, as basically only 'VB*' can be the 0th child of 'VP'
            verb_node = verbal_tree[0]

        # TODO:: may be write this in a for loop??
        if 'MD' in verb_node.label():
            return verb_node
            # TODO:: can/MD do/VB
        if 'VB' in verb_node.label():
            return verb_node
        else:
            return None

            # @staticmethod
            # def morphify(word, org_pos, target_pos):
            # """
            # morph a word based on rules
            # http://stackoverflow.com/questions/27852969/how-to-list-all-the-forms-of-a-word-using-nltk-in-python


class ProcessedText:
    """
    Maybe use nltk.stem.wordnet.WordNetLemmatizer instead of PorterStemmer.
    As stemmer semms just truncate the last parts, 'wolves' to 'wolv' not 'wolf'.
    But we will need to specify pos tag, like lemmatize('running'[,'n']) will be 'running'
     when lemmatize('running', 'v') will be 'run'. This is not what we want,
     like we want 'hypothesis test' to be matched with 'hypothesis testing'.
    """

    def __init__(self, text):
        if type(text) is str:
            self.original_text = text
            self.original_tokens = nltk.word_tokenize(text)
        elif type(text) is list:
            self.original_tokens = text
            self.original_text = NlpUtil.untokenize(text)

        self.stemmed_tokens = None
        self.processed_tokens = None

        self._processing()
        # self.stemmed = self.stemming(text=text, stemmer=stemmer)

    def _processing(self):
        stopwords = nltk.corpus.stopwords.words('english')
        stopwords += list(string.punctuation)

        if not self.stemmed_tokens:
            self._stemming()
        # to lower case and remove stop words
        self.processed_tokens = [t.lower() for t in self.stemmed_tokens if t.lower() not in stopwords]

    def _stemming(self, stemmer=nltk.stem.PorterStemmer()):
        if not self.original_tokens:
            return None
        try:
            self.stemmed_tokens = [stemmer.stem(t) for t in self.original_tokens]
        except UnicodeDecodeError as e:
            raise e
            # self.stemmed_tokens = [stemmer.stem(unicode(t, 'utf-8')) for t in self.original_tokens]

    @staticmethod
    def stemming(text, stemmer=nltk.stem.PorterStemmer()):
        """
            stemming/ to lower case
        :param text: list of tokens
        :param stemmer:
        :return: returned type is the same as input text.
        """
        stopwords = nltk.corpus.stopwords.words('english')
        stopwords += list(string.punctuation)

        if not text:
            return None
        if type(text) is str or unicode:
            original_tokens = nltk.word_tokenize(text)
        elif type(text) is list:  # tokens
            original_tokens = text
        else:
            original_tokens = None

        stemmed_tokens = [stemmer.stem(t.lower()) for t in original_tokens if t.lower() not in stopwords]

        if type(text) is str or unicode:
            stemmed_str = NlpUtil.untokenize(stemmed_tokens)
            return stemmed_str
        elif type(text) is list:
            return stemmed_tokens
        else:
            return None


def test():
    nlutil = NlpUtil()

    sentence = "At eight o'clock on Thursday morning Arthur didn't feel very good. I am good."
    tags = nlutil.pos_tag(sentence)
    print tags


if __name__ == '__main__':
    test()
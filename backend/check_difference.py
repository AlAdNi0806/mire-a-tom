"""
Module difflib -- helpers for computing deltas between objects.

Function get_close_matches(word, possibilities, n=3, cutoff=0.6):
    Use SequenceMatcher to return list of the best "good enough" matches.

Function context_diff(a, b):
    For two lists of strings, return a delta in context diff format.

Function ndiff(a, b):
    Return a delta: the difference between `a` and `b` (lists of strings).

Function restore(delta, which):
    Return one of the two sequences that generated an ndiff delta.

Function unified_diff(a, b):
    For two lists of strings, return a delta in unified diff format.

Class SequenceMatcher:
    A flexible class for comparing pairs of sequences of any type.

Class Differ:
    For producing human-readable deltas from sequences of lines of text.

Class HtmlDiff:
    For producing HTML side by side comparison with change highlights.
"""

__all__ = ['get_close_matches', 'ndiff', 'restore', 'SequenceMatcher',
           'Differ','IS_CHARACTER_JUNK', 'IS_LINE_JUNK', 'context_diff',
           'unified_diff', 'diff_bytes', 'HtmlDiff', 'Match']

from heapq import nlargest as _nlargest
from collections import namedtuple as _namedtuple
from types import GenericAlias

Match = _namedtuple('Match', 'a b size')

def _calculate_ratio(matches, length):
    if length:
        return 2.0 * matches / length
    return 1.0

class SequenceMatcher:

    def __init__(self, isjunk=None, a='', b='', autojunk=True):
        
        self.isjunk = isjunk
        self.a = self.b = None
        self.autojunk = autojunk
        self.set_seqs(a, b)

    def set_seqs(self, a, b):

        self.set_seq1(a)
        self.set_seq2(b)

    def set_seq1(self, a):
        
        if a is self.a:
            return
        self.a = a
        self.matching_blocks = self.opcodes = None

    def set_seq2(self, b):
        
        if b is self.b:
            return
        self.b = b
        self.matching_blocks = self.opcodes = None
        self.fullbcount = None
        self.__chain_b()

    def __chain_b(self):

        b = self.b
        self.b2j = b2j = {}

        for i, elt in enumerate(b):
            indices = b2j.setdefault(elt, [])
            indices.append(i)

        self.bjunk = junk = set()
        isjunk = self.isjunk
        if isjunk:
            for elt in b2j.keys():
                if isjunk(elt):
                    junk.add(elt)
            for elt in junk: # separate loop avoids separate list of keys
                del b2j[elt]

        self.bpopular = popular = set()
        n = len(b)
        if self.autojunk and n >= 200:
            ntest = n // 100 + 1
            for elt, idxs in b2j.items():
                if len(idxs) > ntest:
                    popular.add(elt)
            for elt in popular: # ditto; as fast for 1% deletion
                del b2j[elt]

    def find_longest_match(self, alo=0, ahi=None, blo=0, bhi=None):
        

        a, b, b2j, isbjunk = self.a, self.b, self.b2j, self.bjunk.__contains__
        if ahi is None:
            ahi = len(a)
        if bhi is None:
            bhi = len(b)
        besti, bestj, bestsize = alo, blo, 0
        
        j2len = {}
        nothing = []
        for i in range(alo, ahi):
            j2lenget = j2len.get
            newj2len = {}
            for j in b2j.get(a[i], nothing):
                # a[i] matches b[j]
                if j < blo:
                    continue
                if j >= bhi:
                    break
                k = newj2len[j] = j2lenget(j-1, 0) + 1
                if k > bestsize:
                    besti, bestj, bestsize = i-k+1, j-k+1, k
            j2len = newj2len


        while besti > alo and bestj > blo and \
              not isbjunk(b[bestj-1]) and \
              a[besti-1] == b[bestj-1]:
            besti, bestj, bestsize = besti-1, bestj-1, bestsize+1
        while besti+bestsize < ahi and bestj+bestsize < bhi and \
              not isbjunk(b[bestj+bestsize]) and \
              a[besti+bestsize] == b[bestj+bestsize]:
            bestsize += 1


        while besti > alo and bestj > blo and \
              isbjunk(b[bestj-1]) and \
              a[besti-1] == b[bestj-1]:
            besti, bestj, bestsize = besti-1, bestj-1, bestsize+1
        while besti+bestsize < ahi and bestj+bestsize < bhi and \
              isbjunk(b[bestj+bestsize]) and \
              a[besti+bestsize] == b[bestj+bestsize]:
            bestsize = bestsize + 1

        return Match(besti, bestj, bestsize)

    def get_matching_blocks(self):
        
        if self.matching_blocks is not None:
            return self.matching_blocks
        la, lb = len(self.a), len(self.b)

        queue = [(0, la, 0, lb)]
        matching_blocks = []
        while queue:
            alo, ahi, blo, bhi = queue.pop()
            i, j, k = x = self.find_longest_match(alo, ahi, blo, bhi)
            # a[alo:i] vs b[blo:j] unknown
            # a[i:i+k] same as b[j:j+k]
            # a[i+k:ahi] vs b[j+k:bhi] unknown
            if k:   # if k is 0, there was no matching block
                matching_blocks.append(x)
                if alo < i and blo < j:
                    queue.append((alo, i, blo, j))
                if i+k < ahi and j+k < bhi:
                    queue.append((i+k, ahi, j+k, bhi))
        matching_blocks.sort()

        i1 = j1 = k1 = 0
        non_adjacent = []
        for i2, j2, k2 in matching_blocks:
            if i1 + k1 == i2 and j1 + k1 == j2:

                k1 += k2
            else:

                if k1:
                    non_adjacent.append((i1, j1, k1))
                i1, j1, k1 = i2, j2, k2
        if k1:
            non_adjacent.append((i1, j1, k1))

        non_adjacent.append( (la, lb, 0) )
        self.matching_blocks = list(map(Match._make, non_adjacent))
        return self.matching_blocks

    def get_opcodes(self):
        
        if self.opcodes is not None:
            return self.opcodes
        i = j = 0
        self.opcodes = answer = []
        for ai, bj, size in self.get_matching_blocks():
            
            tag = ''
            if i < ai and j < bj:
                tag = 'replace'
            elif i < ai:
                tag = 'delete'
            elif j < bj:
                tag = 'insert'
            if tag:
                answer.append( (tag, i, ai, j, bj) )
            i, j = ai+size, bj+size
            # the list of matching blocks is terminated by a
            # sentinel with size 0
            if size:
                answer.append( ('equal', ai, i, bj, j) )
        return answer

    def get_grouped_opcodes(self, n=3):
        

        codes = self.get_opcodes()
        if not codes:
            codes = [("equal", 0, 1, 0, 1)]
        # Fixup leading and trailing groups if they show no changes.
        if codes[0][0] == 'equal':
            tag, i1, i2, j1, j2 = codes[0]
            codes[0] = tag, max(i1, i2-n), i2, max(j1, j2-n), j2
        if codes[-1][0] == 'equal':
            tag, i1, i2, j1, j2 = codes[-1]
            codes[-1] = tag, i1, min(i2, i1+n), j1, min(j2, j1+n)

        nn = n + n
        group = []
        for tag, i1, i2, j1, j2 in codes:
            # End the current group and start a new one whenever
            # there is a large range with no changes.
            if tag == 'equal' and i2-i1 > nn:
                group.append((tag, i1, min(i2, i1+n), j1, min(j2, j1+n)))
                yield group
                group = []
                i1, j1 = max(i1, i2-n), max(j1, j2-n)
            group.append((tag, i1, i2, j1 ,j2))
        if group and not (len(group)==1 and group[0][0] == 'equal'):
            yield group

    def ratio(self):
        
        matches = sum(triple[-1] for triple in self.get_matching_blocks())
        return _calculate_ratio(matches, len(self.a) + len(self.b))

    def quick_ratio(self):
        
        if self.fullbcount is None:
            self.fullbcount = fullbcount = {}
            for elt in self.b:
                fullbcount[elt] = fullbcount.get(elt, 0) + 1
        fullbcount = self.fullbcount
        
        avail = {}
        availhas, matches = avail.__contains__, 0
        for elt in self.a:
            if availhas(elt):
                numb = avail[elt]
            else:
                numb = fullbcount.get(elt, 0)
            avail[elt] = numb - 1
            if numb > 0:
                matches = matches + 1
        return _calculate_ratio(matches, len(self.a) + len(self.b))

    def real_quick_ratio(self):
       

        la, lb = len(self.a), len(self.b)
        return _calculate_ratio(min(la, lb), la + lb)

    __class_getitem__ = classmethod(GenericAlias)


def get_close_matches(word, possibilities, n=3, cutoff=0.6):
    if not n >  0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = SequenceMatcher()
    s.set_seq2(word)
    for x in possibilities:
        s.set_seq1(x)
        if s.real_quick_ratio() >= cutoff and \
           s.quick_ratio() >= cutoff and \
           s.ratio() >= cutoff:
            result.append((s.ratio(), x))

    result = _nlargest(n, result)
    return [x for score, x in result]


def _keep_original_ws(s, tag_s):
    return ''.join(
        c if tag_c == " " and c.isspace() else tag_c
        for c, tag_c in zip(s, tag_s)
    )



class Differ:
    
    def __init__(self, linejunk=None, charjunk=None):
        

        self.linejunk = linejunk
        self.charjunk = charjunk

    def compare(self, a, b):
        

        cruncher = SequenceMatcher(self.linejunk, a, b)
        for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
            if tag == 'replace':
                g = self._fancy_replace(a, alo, ahi, b, blo, bhi)
            elif tag == 'delete':
                g = self._dump('-', a, alo, ahi)
            elif tag == 'insert':
                g = self._dump('+', b, blo, bhi)
            elif tag == 'equal':
                g = self._dump(' ', a, alo, ahi)
            else:
                raise ValueError('unknown tag %r' % (tag,))

            yield from g

    def _dump(self, tag, x, lo, hi):
        for i in range(lo, hi):
            yield '%s %s' % (tag, x[i])

    def _plain_replace(self, a, alo, ahi, b, blo, bhi):
        assert alo < ahi and blo < bhi
        if bhi - blo < ahi - alo:
            first  = self._dump('+', b, blo, bhi)
            second = self._dump('-', a, alo, ahi)
        else:
            first  = self._dump('-', a, alo, ahi)
            second = self._dump('+', b, blo, bhi)

        for g in first, second:
            yield from g

    def _fancy_replace(self, a, alo, ahi, b, blo, bhi):
       
        cutoff = 0.74999
        cruncher = SequenceMatcher(self.charjunk)
        crqr = cruncher.real_quick_ratio
        cqr = cruncher.quick_ratio
        cr = cruncher.ratio

        WINDOW = 10
        best_i = best_j = None
        dump_i, dump_j = alo, blo # smallest indices not yet resolved
        for j in range(blo, bhi):
            cruncher.set_seq2(b[j])
            aequiv = alo + (j - blo)
            arange = range(max(aequiv - WINDOW, dump_i),
                           min(aequiv + WINDOW + 1, ahi))
            if not arange: # likely exit if `a` is shorter than `b`
                break
            best_ratio = cutoff
            for i in arange:
                cruncher.set_seq1(a[i])
                if (crqr() > best_ratio
                      and cqr() > best_ratio
                      and cr() > best_ratio):
                    best_i, best_j, best_ratio = i, j, cr()

            if best_i is None:
                continue

            yield from self._fancy_helper(a, dump_i, best_i,
                                          b, dump_j, best_j)
            aelt, belt = a[best_i], b[best_j]
            if aelt != belt:
                atags = btags = ""
                cruncher.set_seqs(aelt, belt)
                for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
                    la, lb = ai2 - ai1, bj2 - bj1
                    if tag == 'replace':
                        atags += '^' * la
                        btags += '^' * lb
                    elif tag == 'delete':
                        atags += '-' * la
                    elif tag == 'insert':
                        btags += '+' * lb
                    elif tag == 'equal':
                        atags += ' ' * la
                        btags += ' ' * lb
                    else:
                        raise ValueError('unknown tag %r' % (tag,))
                yield from self._qformat(aelt, belt, atags, btags)
            else:
                yield '  ' + aelt
            dump_i, dump_j = best_i + 1, best_j + 1
            best_i = best_j = None

        yield from self._fancy_helper(a, dump_i, ahi,
                                      b, dump_j, bhi)

    def _fancy_helper(self, a, alo, ahi, b, blo, bhi):
        g = []
        if alo < ahi:
            if blo < bhi:
                g = self._plain_replace(a, alo, ahi, b, blo, bhi)
            else:
                g = self._dump('-', a, alo, ahi)
        elif blo < bhi:
            g = self._dump('+', b, blo, bhi)

        yield from g

    def _qformat(self, aline, bline, atags, btags):
       
        atags = _keep_original_ws(aline, atags).rstrip()
        btags = _keep_original_ws(bline, btags).rstrip()

        yield "- " + aline
        if atags:
            yield f"? {atags}\n"

        yield "+ " + bline
        if btags:
            yield f"? {btags}\n"


import re

def IS_LINE_JUNK(line, pat=re.compile(r"\s*(?:#\s*)?$").match):
   
    return pat(line) is not None

def IS_CHARACTER_JUNK(ch, ws=" \t"):
   
    return ch in ws


########################################################################
###  Unified Diff
########################################################################

def _format_range_unified(start, stop):
   
    beginning = start + 1     # lines start numbering with one
    length = stop - start
    if length == 1:
        return '{}'.format(beginning)
    if not length:
        beginning -= 1        # empty ranges begin at line just before the range
    return '{},{}'.format(beginning, length)

def unified_diff(a, b, fromfile='', tofile='', fromfiledate='',
                 tofiledate='', n=3, lineterm='\n'):
    r"""
    Compare two sequences of lines; generate the delta as a unified diff.

    Unified diffs are a compact way of showing line changes and a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those with ---, +++, or @@) are
    created with a trailing newline.  This is helpful so that inputs
    created from file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs and outputs have trailing
    newlines.

    For inputs that do not have trailing newlines, set the lineterm
    argument to "" so that the output will be uniformly newline free.

    The unidiff format normally has a header for filenames and modification
    times.  Any or all of these may be specified using strings for
    'fromfile', 'tofile', 'fromfiledate', and 'tofiledate'.
    The modification times are normally expressed in the ISO 8601 format.

    Example:

    >>> for line in unified_diff('one two three four'.split(),
    ...             'zero one tree four'.split(), 'Original', 'Current',
    ...             '2005-01-26 23:30:50', '2010-04-02 10:20:52',
    ...             lineterm=''):
    ...     print(line)                 # doctest: +NORMALIZE_WHITESPACE
    --- Original        2005-01-26 23:30:50
    +++ Current         2010-04-02 10:20:52
    @@ -1,4 +1,4 @@
    +zero
     one
    -two
    -three
    +tree
     four
    """

    _check_types(a, b, fromfile, tofile, fromfiledate, tofiledate, lineterm)
    started = False
    for group in SequenceMatcher(None,a,b).get_grouped_opcodes(n):
        if not started:
            started = True
            fromdate = '\t{}'.format(fromfiledate) if fromfiledate else ''
            todate = '\t{}'.format(tofiledate) if tofiledate else ''
            yield '--- {}{}{}'.format(fromfile, fromdate, lineterm)
            yield '+++ {}{}{}'.format(tofile, todate, lineterm)

        first, last = group[0], group[-1]
        file1_range = _format_range_unified(first[1], last[2])
        file2_range = _format_range_unified(first[3], last[4])
        yield '@@ -{} +{} @@{}'.format(file1_range, file2_range, lineterm)

        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                for line in a[i1:i2]:
                    yield ' ' + line
                continue
            if tag in {'replace', 'delete'}:
                for line in a[i1:i2]:
                    yield '-' + line
            if tag in {'replace', 'insert'}:
                for line in b[j1:j2]:
                    yield '+' + line


########################################################################
###  Context Diff
########################################################################

def _format_range_context(start, stop):
    beginning = start + 1     # lines start numbering with one
    length = stop - start
    if not length:
        beginning -= 1        # empty ranges begin at line just before the range
    if length <= 1:
        return '{}'.format(beginning)
    return '{},{}'.format(beginning, beginning + length - 1)

# See http://www.unix.org/single_unix_specification/
def context_diff(a, b, fromfile='', tofile='',
                 fromfiledate='', tofiledate='', n=3, lineterm='\n'):
    

    _check_types(a, b, fromfile, tofile, fromfiledate, tofiledate, lineterm)
    prefix = dict(insert='+ ', delete='- ', replace='! ', equal='  ')
    started = False
    for group in SequenceMatcher(None,a,b).get_grouped_opcodes(n):
        if not started:
            started = True
            fromdate = '\t{}'.format(fromfiledate) if fromfiledate else ''
            todate = '\t{}'.format(tofiledate) if tofiledate else ''
            yield '*** {}{}{}'.format(fromfile, fromdate, lineterm)
            yield '--- {}{}{}'.format(tofile, todate, lineterm)

        first, last = group[0], group[-1]
        yield '***************' + lineterm

        file1_range = _format_range_context(first[1], last[2])
        yield '*** {} ****{}'.format(file1_range, lineterm)

        if any(tag in {'replace', 'delete'} for tag, _, _, _, _ in group):
            for tag, i1, i2, _, _ in group:
                if tag != 'insert':
                    for line in a[i1:i2]:
                        yield prefix[tag] + line

        file2_range = _format_range_context(first[3], last[4])
        yield '--- {} ----{}'.format(file2_range, lineterm)

        if any(tag in {'replace', 'insert'} for tag, _, _, _, _ in group):
            for tag, _, _, j1, j2 in group:
                if tag != 'delete':
                    for line in b[j1:j2]:
                        yield prefix[tag] + line

def _check_types(a, b, *args):
    
    if a and not isinstance(a[0], str):
        raise TypeError('lines to compare must be str, not %s (%r)' %
                        (type(a[0]).__name__, a[0]))
    if b and not isinstance(b[0], str):
        raise TypeError('lines to compare must be str, not %s (%r)' %
                        (type(b[0]).__name__, b[0]))
    if isinstance(a, str):
        raise TypeError('input must be a sequence of strings, not %s' %
                        type(a).__name__)
    if isinstance(b, str):
        raise TypeError('input must be a sequence of strings, not %s' %
                        type(b).__name__)
    for arg in args:
        if not isinstance(arg, str):
            raise TypeError('all arguments must be str, not: %r' % (arg,))

def diff_bytes(dfunc, a, b, fromfile=b'', tofile=b'',
               fromfiledate=b'', tofiledate=b'', n=3, lineterm=b'\n'):
    
    def decode(s):
        try:
            return s.decode('ascii', 'surrogateescape')
        except AttributeError as err:
            msg = ('all arguments must be bytes, not %s (%r)' %
                   (type(s).__name__, s))
            raise TypeError(msg) from err
    a = list(map(decode, a))
    b = list(map(decode, b))
    fromfile = decode(fromfile)
    tofile = decode(tofile)
    fromfiledate = decode(fromfiledate)
    tofiledate = decode(tofiledate)
    lineterm = decode(lineterm)

    lines = dfunc(a, b, fromfile, tofile, fromfiledate, tofiledate, n, lineterm)
    for line in lines:
        yield line.encode('ascii', 'surrogateescape')

def ndiff(a, b, linejunk=None, charjunk=IS_CHARACTER_JUNK):
    
    return Differ(linejunk, charjunk).compare(a, b)

def _mdiff(fromlines, tolines, context=None, linejunk=None,
           charjunk=IS_CHARACTER_JUNK):
   
    import re

    # regular expression for finding intraline change indices
    change_re = re.compile(r'(\++|\-+|\^+)')

    # create the difference iterator to generate the differences
    diff_lines_iterator = ndiff(fromlines,tolines,linejunk,charjunk)

    def _make_line(lines, format_key, side, num_lines=[0,0]):
        """Returns line of text with user's change markup and line formatting.

        lines -- list of lines from the ndiff generator to produce a line of
                 text from.  When producing the line of text to return, the
                 lines used are removed from this list.
        format_key -- '+' return first line in list with "add" markup around
                          the entire line.
                      '-' return first line in list with "delete" markup around
                          the entire line.
                      '?' return first line in list with add/delete/change
                          intraline markup (indices obtained from second line)
                      None return first line in list with no markup
        side -- indice into the num_lines list (0=from,1=to)
        num_lines -- from/to current line number.  This is NOT intended to be a
                     passed parameter.  It is present as a keyword argument to
                     maintain memory of the current line numbers between calls
                     of this function.

        Note, this function is purposefully not defined at the module scope so
        that data it needs from its parent function (within whose context it
        is defined) does not need to be of module scope.
        """
        num_lines[side] += 1
        # Handle case where no user markup is to be added, just return line of
        # text with user's line format to allow for usage of the line number.
        if format_key is None:
            return (num_lines[side],lines.pop(0)[2:])
        # Handle case of intraline changes
        if format_key == '?':
            text, markers = lines.pop(0), lines.pop(0)
            # find intraline changes (store change type and indices in tuples)
            sub_info = []
            def record_sub_info(match_object,sub_info=sub_info):
                sub_info.append([match_object.group(1)[0],match_object.span()])
                return match_object.group(1)
            change_re.sub(record_sub_info,markers)
            # process each tuple inserting our special marks that won't be
            # noticed by an xml/html escaper.
            for key,(begin,end) in reversed(sub_info):
                text = text[0:begin]+'\0'+key+text[begin:end]+'\1'+text[end:]
            text = text[2:]
        # Handle case of add/delete entire line
        else:
            text = lines.pop(0)[2:]
            # if line of text is just a newline, insert a space so there is
            # something for the user to highlight and see.
            if not text:
                text = ' '
            # insert marks that won't be noticed by an xml/html escaper.
            text = '\0' + format_key + text + '\1'
        # Return line of text, first allow user's line formatter to do its
        # thing (such as adding the line number) then replace the special
        # marks with what the user's change markup.
        return (num_lines[side],text)

    def _line_iterator():
        """Yields from/to lines of text with a change indication.

        This function is an iterator.  It itself pulls lines from a
        differencing iterator, processes them and yields them.  When it can
        it yields both a "from" and a "to" line, otherwise it will yield one
        or the other.  In addition to yielding the lines of from/to text, a
        boolean flag is yielded to indicate if the text line(s) have
        differences in them.

        Note, this function is purposefully not defined at the module scope so
        that data it needs from its parent function (within whose context it
        is defined) does not need to be of module scope.
        """
        lines = []
        num_blanks_pending, num_blanks_to_yield = 0, 0
        while True:
            # Load up next 4 lines so we can look ahead, create strings which
            # are a concatenation of the first character of each of the 4 lines
            # so we can do some very readable comparisons.
            while len(lines) < 4:
                lines.append(next(diff_lines_iterator, 'X'))
            s = ''.join([line[0] for line in lines])
            if s.startswith('X'):
                # When no more lines, pump out any remaining blank lines so the
                # corresponding add/delete lines get a matching blank line so
                # all line pairs get yielded at the next level.
                num_blanks_to_yield = num_blanks_pending
            elif s.startswith('-?+?'):
                # simple intraline change
                yield _make_line(lines,'?',0), _make_line(lines,'?',1), True
                continue
            elif s.startswith('--++'):
                # in delete block, add block coming: we do NOT want to get
                # caught up on blank lines yet, just process the delete line
                num_blanks_pending -= 1
                yield _make_line(lines,'-',0), None, True
                continue
            elif s.startswith(('--?+', '--+', '- ')):
                # in delete block and see an intraline change or unchanged line
                # coming: yield the delete line and then blanks
                from_line,to_line = _make_line(lines,'-',0), None
                num_blanks_to_yield,num_blanks_pending = num_blanks_pending-1,0
            elif s.startswith('-+?'):
                # intraline change
                yield _make_line(lines,None,0), _make_line(lines,'?',1), True
                continue
            elif s.startswith('-?+'):
                # intraline change
                yield _make_line(lines,'?',0), _make_line(lines,None,1), True
                continue
            elif s.startswith('-'):
                # delete FROM line
                num_blanks_pending -= 1
                yield _make_line(lines,'-',0), None, True
                continue
            elif s.startswith('+--'):
                # in add block, delete block coming: we do NOT want to get
                # caught up on blank lines yet, just process the add line
                num_blanks_pending += 1
                yield None, _make_line(lines,'+',1), True
                continue
            elif s.startswith(('+ ', '+-')):
                # will be leaving an add block: yield blanks then add line
                from_line, to_line = None, _make_line(lines,'+',1)
                num_blanks_to_yield,num_blanks_pending = num_blanks_pending+1,0
            elif s.startswith('+'):
                # inside an add block, yield the add line
                num_blanks_pending += 1
                yield None, _make_line(lines,'+',1), True
                continue
            elif s.startswith(' '):
                # unchanged text, yield it to both sides
                yield _make_line(lines[:],None,0),_make_line(lines,None,1),False
                continue
            # Catch up on the blank lines so when we yield the next from/to
            # pair, they are lined up.
            while(num_blanks_to_yield < 0):
                num_blanks_to_yield += 1
                yield None,('','\n'),True
            while(num_blanks_to_yield > 0):
                num_blanks_to_yield -= 1
                yield ('','\n'),None,True
            if s.startswith('X'):
                return
            else:
                yield from_line,to_line,True

    def _line_pair_iterator():
        """Yields from/to lines of text with a change indication.

        This function is an iterator.  It itself pulls lines from the line
        iterator.  Its difference from that iterator is that this function
        always yields a pair of from/to text lines (with the change
        indication).  If necessary it will collect single from/to lines
        until it has a matching pair from/to pair to yield.

        Note, this function is purposefully not defined at the module scope so
        that data it needs from its parent function (within whose context it
        is defined) does not need to be of module scope.
        """
        line_iterator = _line_iterator()
        fromlines,tolines=[],[]
        while True:
            # Collecting lines of text until we have a from/to pair
            while (len(fromlines)==0 or len(tolines)==0):
                try:
                    from_line, to_line, found_diff = next(line_iterator)
                except StopIteration:
                    return
                if from_line is not None:
                    fromlines.append((from_line,found_diff))
                if to_line is not None:
                    tolines.append((to_line,found_diff))
            # Once we have a pair, remove them from the collection and yield it
            from_line, fromDiff = fromlines.pop(0)
            to_line, to_diff = tolines.pop(0)
            yield (from_line,to_line,fromDiff or to_diff)

    # Handle case where user does not want context differencing, just yield
    # them up without doing anything else with them.
    line_pair_iterator = _line_pair_iterator()
    if context is None:
        yield from line_pair_iterator
    # Handle case where user wants context differencing.  We must do some
    # storage of lines until we know for sure that they are to be yielded.
    else:
        context += 1
        lines_to_write = 0
        while True:
            # Store lines up until we find a difference, note use of a
            # circular queue because we only need to keep around what
            # we need for context.
            index, contextLines = 0, [None]*(context)
            found_diff = False
            while(found_diff is False):
                try:
                    from_line, to_line, found_diff = next(line_pair_iterator)
                except StopIteration:
                    return
                i = index % context
                contextLines[i] = (from_line, to_line, found_diff)
                index += 1
            # Yield lines that we have collected so far, but first yield
            # the user's separator.
            if index > context:
                yield None, None, None
                lines_to_write = context
            else:
                lines_to_write = index
                index = 0
            while(lines_to_write):
                i = index % context
                index += 1
                yield contextLines[i]
                lines_to_write -= 1
            # Now yield the context lines after the change
            lines_to_write = context-1
            try:
                while(lines_to_write):
                    from_line, to_line, found_diff = next(line_pair_iterator)
                    # If another change within the context, extend the context
                    if found_diff:
                        lines_to_write = context-1
                    else:
                        lines_to_write -= 1
                    yield from_line, to_line, found_diff
            except StopIteration:
                # Catch exception from next() and return normally
                return


_file_template = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>

<head>
    <meta http-equiv="Content-Type"
          content="text/html; charset=%(charset)s" />
    <title></title>
    <style type="text/css">%(styles)s
    </style>
</head>

<body>
    %(table)s%(legend)s
</body>

</html>"""

_styles = """
        table.diff {font-family:Courier; border:medium;}
        .diff_header {background-color:#e0e0e0}
        td.diff_header {text-align:right}
        .diff_next {background-color:#c0c0c0}
        .diff_add {background-color:#aaffaa}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}"""

_table_template = """
    <table class="diff" id="difflib_chg_%(prefix)s_top"
           cellspacing="0" cellpadding="0" rules="groups" >
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        %(header_row)s
        <tbody>
%(data_rows)s        </tbody>
    </table>"""

_legend = """
    <table class="diff" summary="Legends">
        <tr> <th colspan="2"> Legends </th> </tr>
        <tr> <td> <table border="" summary="Colors">
                      <tr><th> Colors </th> </tr>
                      <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>
                      <tr><td class="diff_chg">Changed</td> </tr>
                      <tr><td class="diff_sub">Deleted</td> </tr>
                  </table></td>
             <td> <table border="" summary="Links">
                      <tr><th colspan="2"> Links </th> </tr>
                      <tr><td>(f)irst change</td> </tr>
                      <tr><td>(n)ext change</td> </tr>
                      <tr><td>(t)op</td> </tr>
                  </table></td> </tr>
    </table>"""

class HtmlDiff(object):
    """For producing HTML side by side comparison with change highlights.

    This class can be used to create an HTML table (or a complete HTML file
    containing the table) showing a side by side, line by line comparison
    of text with inter-line and intra-line change highlights.  The table can
    be generated in either full or contextual difference mode.

    The following methods are provided for HTML generation:

    make_table -- generates HTML for a single side by side table
    make_file -- generates complete HTML file with a single side by side table

    See tools/scripts/diff.py for an example usage of this class.
    """

    _file_template = _file_template
    _styles = _styles
    _table_template = _table_template
    _legend = _legend
    _default_prefix = 0

    def __init__(self,tabsize=8,wrapcolumn=None,linejunk=None,
                 charjunk=IS_CHARACTER_JUNK):
        """HtmlDiff instance initializer

        Arguments:
        tabsize -- tab stop spacing, defaults to 8.
        wrapcolumn -- column number where lines are broken and wrapped,
            defaults to None where lines are not wrapped.
        linejunk,charjunk -- keyword arguments passed into ndiff() (used by
            HtmlDiff() to generate the side by side HTML differences).  See
            ndiff() documentation for argument default values and descriptions.
        """
        self._tabsize = tabsize
        self._wrapcolumn = wrapcolumn
        self._linejunk = linejunk
        self._charjunk = charjunk

    def make_file(self, fromlines, tolines, fromdesc='', todesc='',
                  context=False, numlines=5, *, charset='utf-8'):
        """Returns HTML file of side by side comparison with change highlights

        Arguments:
        fromlines -- list of "from" lines
        tolines -- list of "to" lines
        fromdesc -- "from" file column header string
        todesc -- "to" file column header string
        context -- set to True for contextual differences (defaults to False
            which shows full differences).
        numlines -- number of context lines.  When context is set True,
            controls number of lines displayed before and after the change.
            When context is False, controls the number of lines to place
            the "next" link anchors before the next change (so click of
            "next" link jumps to just before the change).
        charset -- charset of the HTML document
        """

        return (self._file_template % dict(
            styles=self._styles,
            legend=self._legend,
            table=self.make_table(fromlines, tolines, fromdesc, todesc,
                                  context=context, numlines=numlines),
            charset=charset
        )).encode(charset, 'xmlcharrefreplace').decode(charset)

    def _tab_newline_replace(self,fromlines,tolines):
        """Returns from/to line lists with tabs expanded and newlines removed.

        Instead of tab characters being replaced by the number of spaces
        needed to fill in to the next tab stop, this function will fill
        the space with tab characters.  This is done so that the difference
        algorithms can identify changes in a file when tabs are replaced by
        spaces and vice versa.  At the end of the HTML generation, the tab
        characters will be replaced with a nonbreakable space.
        """
        def expand_tabs(line):
            # hide real spaces
            line = line.replace(' ','\0')
            # expand tabs into spaces
            line = line.expandtabs(self._tabsize)
            # replace spaces from expanded tabs back into tab characters
            # (we'll replace them with markup after we do differencing)
            line = line.replace(' ','\t')
            return line.replace('\0',' ').rstrip('\n')
        fromlines = [expand_tabs(line) for line in fromlines]
        tolines = [expand_tabs(line) for line in tolines]
        return fromlines,tolines

    def _split_line(self,data_list,line_num,text):
        """Builds list of text lines by splitting text lines at wrap point

        This function will determine if the input text line needs to be
        wrapped (split) into separate lines.  If so, the first wrap point
        will be determined and the first line appended to the output
        text line list.  This function is used recursively to handle
        the second part of the split line to further split it.
        """
        # if blank line or context separator, just add it to the output list
        if not line_num:
            data_list.append((line_num,text))
            return

        # if line text doesn't need wrapping, just add it to the output list
        size = len(text)
        max = self._wrapcolumn
        if (size <= max) or ((size -(text.count('\0')*3)) <= max):
            data_list.append((line_num,text))
            return

        # scan text looking for the wrap point, keeping track if the wrap
        # point is inside markers
        i = 0
        n = 0
        mark = ''
        while n < max and i < size:
            if text[i] == '\0':
                i += 1
                mark = text[i]
                i += 1
            elif text[i] == '\1':
                i += 1
                mark = ''
            else:
                i += 1
                n += 1

        # wrap point is inside text, break it up into separate lines
        line1 = text[:i]
        line2 = text[i:]

        # if wrap point is inside markers, place end marker at end of first
        # line and start marker at beginning of second line because each
        # line will have its own table tag markup around it.
        if mark:
            line1 = line1 + '\1'
            line2 = '\0' + mark + line2

        # tack on first line onto the output list
        data_list.append((line_num,line1))

        # use this routine again to wrap the remaining text
        self._split_line(data_list,'>',line2)

    def _line_wrapper(self,diffs):
        """Returns iterator that splits (wraps) mdiff text lines"""

        # pull from/to data and flags from mdiff iterator
        for fromdata,todata,flag in diffs:
            # check for context separators and pass them through
            if flag is None:
                yield fromdata,todata,flag
                continue
            (fromline,fromtext),(toline,totext) = fromdata,todata
            # for each from/to line split it at the wrap column to form
            # list of text lines.
            fromlist,tolist = [],[]
            self._split_line(fromlist,fromline,fromtext)
            self._split_line(tolist,toline,totext)
            # yield from/to line in pairs inserting blank lines as
            # necessary when one side has more wrapped lines
            while fromlist or tolist:
                if fromlist:
                    fromdata = fromlist.pop(0)
                else:
                    fromdata = ('',' ')
                if tolist:
                    todata = tolist.pop(0)
                else:
                    todata = ('',' ')
                yield fromdata,todata,flag

    def _collect_lines(self,diffs):
        """Collects mdiff output into separate lists

        Before storing the mdiff from/to data into a list, it is converted
        into a single line of text with HTML markup.
        """

        fromlist,tolist,flaglist = [],[],[]
        # pull from/to data and flags from mdiff style iterator
        for fromdata,todata,flag in diffs:
            try:
                # store HTML markup of the lines into the lists
                fromlist.append(self._format_line(0,flag,*fromdata))
                tolist.append(self._format_line(1,flag,*todata))
            except TypeError:
                # exceptions occur for lines where context separators go
                fromlist.append(None)
                tolist.append(None)
            flaglist.append(flag)
        return fromlist,tolist,flaglist

    def _format_line(self,side,flag,linenum,text):
        """Returns HTML markup of "from" / "to" text lines

        side -- 0 or 1 indicating "from" or "to" text
        flag -- indicates if difference on line
        linenum -- line number (used for line number column)
        text -- line text to be marked up
        """
        try:
            linenum = '%d' % linenum
            id = ' id="%s%s"' % (self._prefix[side],linenum)
        except TypeError:
            # handle blank lines where linenum is '>' or ''
            id = ''
        # replace those things that would get confused with HTML symbols
        text=text.replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")

        # make space non-breakable so they don't get compressed or line wrapped
        text = text.replace(' ','&nbsp;').rstrip()

        return '<td class="diff_header"%s>%s</td><td nowrap="nowrap">%s</td>' \
               % (id,linenum,text)

    def _make_prefix(self):
        """Create unique anchor prefixes"""

        # Generate a unique anchor prefix so multiple tables
        # can exist on the same HTML page without conflicts.
        fromprefix = "from%d_" % HtmlDiff._default_prefix
        toprefix = "to%d_" % HtmlDiff._default_prefix
        HtmlDiff._default_prefix += 1
        # store prefixes so line format method has access
        self._prefix = [fromprefix,toprefix]

    def _convert_flags(self,fromlist,tolist,flaglist,context,numlines):
        """Makes list of "next" links"""

        # all anchor names will be generated using the unique "to" prefix
        toprefix = self._prefix[1]

        # process change flags, generating middle column of next anchors/links
        next_id = ['']*len(flaglist)
        next_href = ['']*len(flaglist)
        num_chg, in_change = 0, False
        last = 0
        for i,flag in enumerate(flaglist):
            if flag:
                if not in_change:
                    in_change = True
                    last = i
                    # at the beginning of a change, drop an anchor a few lines
                    # (the context lines) before the change for the previous
                    # link
                    i = max([0,i-numlines])
                    next_id[i] = ' id="difflib_chg_%s_%d"' % (toprefix,num_chg)
                    # at the beginning of a change, drop a link to the next
                    # change
                    num_chg += 1
                    next_href[last] = '<a href="#difflib_chg_%s_%d">n</a>' % (
                         toprefix,num_chg)
            else:
                in_change = False
        # check for cases where there is no content to avoid exceptions
        if not flaglist:
            flaglist = [False]
            next_id = ['']
            next_href = ['']
            last = 0
            if context:
                fromlist = ['<td></td><td>&nbsp;No Differences Found&nbsp;</td>']
                tolist = fromlist
            else:
                fromlist = tolist = ['<td></td><td>&nbsp;Empty File&nbsp;</td>']
        # if not a change on first line, drop a link
        if not flaglist[0]:
            next_href[0] = '<a href="#difflib_chg_%s_0">f</a>' % toprefix
        # redo the last link to link to the top
        next_href[last] = '<a href="#difflib_chg_%s_top">t</a>' % (toprefix)

        return fromlist,tolist,flaglist,next_href,next_id

    def make_table(self,fromlines,tolines,fromdesc='',todesc='',context=False,
                   numlines=5):
        """Returns HTML table of side by side comparison with change highlights

        Arguments:
        fromlines -- list of "from" lines
        tolines -- list of "to" lines
        fromdesc -- "from" file column header string
        todesc -- "to" file column header string
        context -- set to True for contextual differences (defaults to False
            which shows full differences).
        numlines -- number of context lines.  When context is set True,
            controls number of lines displayed before and after the change.
            When context is False, controls the number of lines to place
            the "next" link anchors before the next change (so click of
            "next" link jumps to just before the change).
        """

        # make unique anchor prefixes so that multiple tables may exist
        # on the same page without conflict.
        self._make_prefix()

        fromlines,tolines = self._tab_newline_replace(fromlines,tolines)

        if context:
            context_lines = numlines
        else:
            context_lines = None
        diffs = _mdiff(fromlines,tolines,context_lines,linejunk=self._linejunk,
                      charjunk=self._charjunk)

        if self._wrapcolumn:
            diffs = self._line_wrapper(diffs)

        fromlist,tolist,flaglist = self._collect_lines(diffs)

        fromlist,tolist,flaglist,next_href,next_id = self._convert_flags(
            fromlist,tolist,flaglist,context,numlines)

        s = []
        fmt = '            <tr><td class="diff_next"%s>%s</td>%s' + \
              '<td class="diff_next">%s</td>%s</tr>\n'
        for i in range(len(flaglist)):
            if flaglist[i] is None:
                if i > 0:
                    s.append('        </tbody>        \n        <tbody>\n')
            else:
                s.append( fmt % (next_id[i],next_href[i],fromlist[i],
                                           next_href[i],tolist[i]))
        if fromdesc or todesc:
            header_row = '<thead><tr>%s%s%s%s</tr></thead>' % (
                '<th class="diff_next"><br /></th>',
                '<th colspan="2" class="diff_header">%s</th>' % fromdesc,
                '<th class="diff_next"><br /></th>',
                '<th colspan="2" class="diff_header">%s</th>' % todesc)
        else:
            header_row = ''

        table = self._table_template % dict(
            data_rows=''.join(s),
            header_row=header_row,
            prefix=self._prefix[1])

        return table.replace('\0+','<span class="diff_add">'). \
                     replace('\0-','<span class="diff_sub">'). \
                     replace('\0^','<span class="diff_chg">'). \
                     replace('\1','</span>'). \
                     replace('\t','&nbsp;')

del re

def restore(delta, which):

    try:
        tag = {1: "- ", 2: "+ "}[int(which)]
    except KeyError:
        raise ValueError('unknown delta choice (must be 1 or 2): %r'
                           % which) from None
    prefixes = ("  ", tag)
    for line in delta:
        if line[:2] in prefixes:
            yield line[2:]

def _test():
    import doctest, difflib
    return doctest.testmod(difflib)

if __name__ == "__main__":
    _test()
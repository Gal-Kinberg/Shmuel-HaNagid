from dataclasses import dataclass, asdict, field
import json

@dataclass(frozen=True, kw_only=True)
class Apparatus:
    """
    Represents an apparatus, usually a textual commentary or annotation related to a specific song,
    line, or passage of text. Ensures immutability with frozen dataclass and keyword-only argument behavior.

    The ``Apparatus`` class is used to encapsulate information such as the song name, specific line,
    lemma, source, target, and optional comment. By default, the type is predefined as "apparatus"
    and cannot be modified externally.

    :ivar song_name: The name of the song associated with this apparatus.
    :type song_name: str
    :ivar line: The line number in the song corresponding to this apparatus.
    :type line: int
    :ivar lemma: The lemma or a specific word/phrase in the song being annotated.
    :type lemma: str
    :ivar source: The original text or source information for this apparatus.
    :type source: str
    :ivar target: The target text or translation/resulting text for this apparatus.
    :type target: str
    :ivar comment: An optional comment or annotation related to this apparatus.
    :type comment: str | None
    :ivar type: A fixed value indicating the class of the apparatus, defaulting to "apparatus".
    :type type: str
    """
    song_name: str
    line: int
    lemma: str
    source: str
    target: str
    comment: str | None = None
    type: str = field(default="apparatus", init=False)

    def to_dict(self):
        """
        Converts the Apparatus instance to a dictionary.
        """
        return asdict(self)

    def to_json(self):
        """
        Converts the Apparatus instance to a JSON string.
        """
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)

@dataclass(frozen=True)
class MissingApparatus(Apparatus):
    type: str = field(default="missing", init=False)

@dataclass(frozen=True)
class FullSpellingApparatus(Apparatus):
    text: str
    type: str = field(default="full_spelling", init=False)

@dataclass(frozen=True)
class LetterSwapApparatus(Apparatus):
    text: str
    old_letter: str
    new_letter: str
    type: str = field(default="letter_swap", init=False)

@dataclass(frozen=True)
class WordSwapApparatus(Apparatus):
    text: str
    # new_word: str
    type: str = field(default="word_swap", init=False)

@dataclass(frozen=True)
class OrderSwapApparatus(Apparatus):
    text: str
    type: str = field(default="order_swap", init=False)

@dataclass(frozen=True)
class DeletionApparatus(Apparatus):
    deleted: str
    corrected: str
    type: str = field(default="deletion", init=False)
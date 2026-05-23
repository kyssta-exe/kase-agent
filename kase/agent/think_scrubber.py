"""Streaming think/reasoning block scrubber."""

import re

_OPEN_TAGS = ("<think>", "<thinking>", "<reasoning>", "<REASONING_SCRATCHPAD>")
_CLOSE_TAGS = ("</think>", "</thinking>", "</reasoning>", "</REASONING_SCRATCHPAD>")


class StreamingThinkScrubber:
    def __init__(self):
        self._buffer = ""
        self._in_block = False
    
    def process(self, chunk: str) -> str:
        self._buffer += chunk
        
        if not self._in_block:
            earliest_open = -1
            for tag in _OPEN_TAGS:
                pos = self._buffer.find(tag)
                if pos != -1 and (earliest_open == -1 or pos < earliest_open):
                    earliest_open = pos
            
            if earliest_open != -1:
                before = self._buffer[:earliest_open]
                self._buffer = self._buffer[earliest_open:]
                self._in_block = True
                return before
        
        if self._in_block:
            earliest_close = -1
            earliest_tag = ""
            for tag in _CLOSE_TAGS:
                pos = self._buffer.find(tag)
                if pos != -1 and (earliest_close == -1 or pos < earliest_close):
                    earliest_close = pos
                    earliest_tag = tag
            
            if earliest_close != -1:
                after = self._buffer[earliest_close + len(earliest_tag):]
                self._buffer = after
                self._in_block = False
                return self.process("")
        
        return ""
    
    def flush(self) -> str:
        if self._in_block:
            self._in_block = False
            self._buffer = ""
        return ""


def strip_think_blocks(text: str) -> str:
    for tag in _OPEN_TAGS + _CLOSE_TAGS:
        text = text.replace(tag, "")
    return text

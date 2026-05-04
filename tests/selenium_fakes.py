"""Shared mock Selenium helpers — importable from any test module.

These are NOT pytest fixtures. Use them directly when constructing test data.
"""

from __future__ import annotations

import re


class FakeWebElement:
    """Unified mock for a Selenium WebElement.

    Supports both upward DOM traversal (via XPATH — returns parent) and
    downward lookup by data-testid (via CSS selector — returns matching child).
    """

    def __init__(self, text='', attrs=None, parent=None, children=None):
        self._text = text
        self._attrs = attrs or {}
        self._parent = parent
        self._children = children or []

    @property
    def text(self):
        return self._text

    def get_attribute(self, name):
        return self._attrs.get(name)

    def find_element(self, by=None, value=None, *_extra):
        by_str = str(by or '').lower()

        # XPATH: simulate ancestor traversal by returning the parent element
        if 'xpath' in by_str:
            if self._parent is not None:
                return self._parent
            raise RuntimeError('no parent element')

        # CSS selector: look up a child by data-testid attribute
        selector = str(value or '')
        match = re.search(r"data-testid='([^']+)'", selector)
        if match:
            found = self._find_child_by_testid(match.group(1))
            if found:
                return found

        return self._children[0] if self._children else self

    def _find_child_by_testid(self, testid: str) -> FakeWebElement | None:
        for child in self._children:
            if getattr(child, '_attrs', {}).get('data-testid') == testid:
                return child
            result = child._find_child_by_testid(testid)
            if result:
                return result
        return None

    def find_elements(self, *_args):
        return self._children


class FakeDriver:
    """Mock Selenium WebDriver that returns a fixed list of elements."""

    def __init__(self, elements):
        self._elements = elements

    def find_elements(self, *_args):
        return self._elements

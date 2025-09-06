"""
    test_locale
    ~~~~~~~~~~

    Test locale.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx import locale


@pytest.fixture(autouse=True)
def cleanup_translations():
    yield
    locale.translators.clear()


def test_init(rootdir):
    # not initialized yet
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'Hello world'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'

    # load locale1
    locale.init([rootdir / 'test-locale' / 'locale1'], 'en', 'myext')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'

    # load a catalog to unrelated namespace
    locale.init([rootdir / 'test-locale' / 'locale2'], 'en', 'myext', 'mynamespace')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'Hello sphinx'  # nothing changed here
    assert _('Hello reST') == 'Hello reST'

    # load locale2 in addition
    locale.init([rootdir / 'test-locale' / 'locale2'], 'en', 'myext')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'HELLO SPHINX'
    assert _('Hello reST') == 'Hello reST'


def test_init_with_unknown_language(rootdir):
    locale.init([rootdir / 'test-locale' / 'locale1'], 'unknown', 'myext')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'Hello world'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'


def test_add_message_catalog(app, rootdir):
    app.config.language = 'en'
    app.add_message_catalog('myext', rootdir / 'test-locale' / 'locale1')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'


def test_user_locale_override_builtin():
    """Test that user-provided locale directories take precedence over built-in Sphinx locales."""
    import os
    import tempfile
    from pathlib import Path
    
    # Create temporary locale directory with custom sphinx translations
    with tempfile.TemporaryDirectory() as tmpdir:
        locale_dir = Path(tmpdir) / 'locale'
        locale_dir.mkdir()
        
        # Create English locale directory structure
        en_dir = locale_dir / 'en' / 'LC_MESSAGES'
        en_dir.mkdir(parents=True)
        
        # Create a custom sphinx.po file
        po_content = '''msgid "Fig. %s"
msgstr "Custom Figure %s"

msgid "Listing %s" 
msgstr "Custom Listing %s"'''
        
        po_file = en_dir / 'sphinx.po'
        with open(po_file, 'w') as f:
            f.write(po_content)
        
        # Create MO file from PO file
        from babel.messages.pofile import read_po
        from babel.messages.mofile import write_mo
        
        with open(po_file, 'rb') as f:
            catalog = read_po(f)
        
        mo_file = en_dir / 'sphinx.mo'
        with open(mo_file, 'wb') as f:
            write_mo(f, catalog)
        
        # Test that custom translations take precedence
        # First, get built-in sphinx package locale dir
        import sphinx
        sphinx_locale_dir = Path(sphinx.__file__).parent / 'locale'
        
        # Test with user locale dir first (should use custom translations)
        locale.init([str(locale_dir), str(sphinx_locale_dir)], 'en', 'sphinx')
        _ = locale.get_translation('sphinx')
        
        # Should use our custom translations
        assert _('Fig. %s') == 'Custom Figure %s'
        assert _('Listing %s') == 'Custom Listing %s'
        
        # Clear translators for next test
        locale.translators.clear()
        
        # Test with built-in locale dir first (should use built-in translations)
        locale.init([str(sphinx_locale_dir), str(locale_dir)], 'en', 'sphinx')
        _ = locale.get_translation('sphinx')
        
        # Should use built-in translations (Fig. %s in English just stays as is, but we test the pattern)
        # The key point is that it should NOT use our custom translations
        assert _('Fig. %s') != 'Custom Figure %s'
        assert _('Listing %s') != 'Custom Listing %s'

plugin for SynWrite.
gives spell-checking by using Enchant/PyEnchant libraries. it uses Hunspell dictionaries. plugin has also binary DLL files for Windows (32-bit).

misspelled words hilited with red back-color.
to run spell-check use "Plugins" menu:

- call command "Show highlights on/off": this enables spell-check after each change of text, after a 2-3 sec pause (pause after last change of text, so you must stop typing text and wait).
- call command "Check text": this runs one spell-check, and with replace-prompt-dialog. dialog will give suggestions from spell-check engine.


feature: not all text is checked, only words of "comments" and "strings".
see Synwrite help file, how to configure syntax comments and strings for lexers.

author: Alexey T (Synwrite)
license: MIT

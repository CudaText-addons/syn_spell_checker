# coding: utf8
import os
import sys
import string
import json
from .jsoncomment import JsonComment
from .colorcode import *
from sw import *

json_parser = JsonComment(json)

filename_ini = os.path.join(app_ini_dir(), 'syn_spell_checker.ini')
op_lang = ini_read(filename_ini, 'op', 'lang', 'en_US')
op_confirm_esc = ini_read(filename_ini, 'op', 'confirm_esc_key', '0')
op_file_types = ini_read(filename_ini, 'op', 'file_extension_list', '*')
op_color_back = ini_read(filename_ini, 'op', 'color_back', '#eaaaaa')

sys.path.append(os.path.dirname(__file__))
try:
    import enchant
    dict_obj = enchant.Dict(op_lang)
except Exception as ex:
    msg_box(str(ex), MB_OK+MB_ICONERROR)


def is_word_char(s):
    return s.isalpha() or (s in "'_"+string.digits)
    
def is_word_alpha(s):
    if not s: return False    
    #don't allow digit in word
    #don't allow lead-quote
    digits = string.digits+'_'
    for ch in s:
        if ch in digits: return False
    if s[0] in "'": return False
    return True    


def dlg_spell(sub):
    rep_list = dict_obj.suggest(sub)
    en_list = bool(rep_list)
    if not en_list: rep_list=[]
    
    c1 = chr(1)
    id_edit = 3
    id_list = 5
    id_skip = 6
    id_replace = 7
    id_add = 8
    id_cancel = 9
    res = dlg_custom('Misspelled word', 426, 306, '\n'.join([]
        +[c1.join(['type=label', 'pos=6,8,100,0', 'cap=Not found:'])]
        +[c1.join(['type=edit', 'pos=106,6,300,0', 'cap='+sub, 'props=1,0,1'])]
        +[c1.join(['type=label', 'pos=6,38,100,0', 'cap=C&ustom text:'])]
        +[c1.join(['type=edit', 'pos=106,36,300,0', 'val='])]
        +[c1.join(['type=label', 'pos=6,68,100,0', 'cap=Su&ggestions:'])]
        +[c1.join(['type=listbox', 'pos=106,66,300,300', 'items='+'\t'.join(rep_list), 'val='+('0' if en_list else '-1')])]
        +[c1.join(['type=button', 'pos=306,66,420,0', 'cap=&Ignore', 'props=1'])]
        +[c1.join(['type=button', 'pos=306,96,420,0', 'cap=&Change'])]
        +[c1.join(['type=button', 'pos=306,126,420,0', 'cap=&Add'])]
        +[c1.join(['type=button', 'pos=306,186,420,0', 'cap=Cancel'])]
        ), 3) 
        
    if res is None: return
    res, text = res
    text = text.splitlines()
    
    if res==id_skip:
        return ''
        
    if res==id_add:
        dict_obj.add_to_pwl(sub)
        return ''
        
    if res==id_replace:
        word = text[id_edit]
        if word:
            return word
        if en_list: 
            return rep_list[int(text[id_list])]
        else:
            return ''
            

def dlg_select_dict():
    items = sorted(enchant.list_languages())
    res = dlg_menu(MENU_SIMPLE, 'Langs', '\n'.join(items))
    if res is None: return
    return items[res]
    

def is_filetype_ok(fn):
    global op_file_types
    if op_file_types=='': return False
    if op_file_types=='*': return True
    if fn=='': return True #allow in untitled tabs
    fn = os.path.basename(fn)
    n = fn.rfind('.')
    if n<0: return True #allow if no extension
    fn = fn[n+1:]
    return ','+fn+',' in ','+op_file_types+','


def do_work(with_dialog=False):
    global op_confirm_esc
    global op_color_back
    
    ed.set_attr(ATTRIB_CLEAR_ALL, 0)
    count_all = 0
    count_replace = 0
    total_lines = ed.get_line_count()
    percent = 0
    app_proc(PROC_SET_ESCAPE, '0')
    
    prev_pos = ed.get_caret_xy()
    prev_sel = ed.get_sel()
    
    for nline in range(total_lines):
        percent_new = nline * 100 // total_lines
        if percent_new!=percent:
            percent = percent_new
            msg_status('Spell-checking %d%%'% percent)
            if app_proc(PROC_GET_ESCAPE, ''):
                app_proc(PROC_SET_ESCAPE, '0')
                if op_confirm_esc=='0' or msg_box(MSG_CONFIRM_Q, 'Stop spell-checking?'):
                    msg_status('Spell-check stopped')
                    return
            
        line = ed.get_text_line(nline)
        n1 = -1
        n2 = -1
        while True:
            n1 += 1
            if n1>=len(line): break
            if not is_word_char(line[n1]): continue
            n2 = n1+1
            while n2<len(line) and is_word_char(line[n2]): n2+=1
            
            #strip quote from begin of word
            if line[n1]=="'": n1 += 1
            #strip quote from end of word
            if line[n2-1]=="'": n2 -= 1
            
            text_x = n1
            text_y = nline

            sub = line[n1:n2]
            n1 = n2
                                       
            noffset = ed.xy_pos(text_x, text_y)
            token = ed.get_prop(PROP_TOKEN_TYPE, str(noffset)) 
            if token not in ['c', 's']: continue
            
            if not is_word_alpha(sub): continue
            if dict_obj.check(sub): continue

            count_all += 1            
            if with_dialog:
                ed.set_sel(ed.xy_pos(text_x, text_y), len(sub))
                rep = dlg_spell(sub)
                if rep is None: return
                if rep=='': continue
                count_replace += 1
                ed.replace(ed.xy_pos(text_x, text_y), len(sub), rep)
                
                #replace
                line = ed.get_text_line(nline)
                n1 += len(rep)-len(sub)
            else:
                ed.set_sel(ed.xy_pos(text_x, text_y), len(sub), True)
                ed.set_attr(ATTRIB_COLOR_BG, html_color_to_int(op_color_back)) 
    
    global op_lang
    msg_status('Spell-check: %s, %d mistakes, %d replaces' % (op_lang, count_all, count_replace))
    ed.set_caret_xy(*prev_pos)
    ed.set_sel(prev_sel[0], prev_sel[1], True)


def do_work_if_name(ed_self):
    if is_filetype_ok(ed_self.get_filename()): 
        do_work()


def do_work_word(with_dialog=False):
    x, y = ed.get_caret_xy()
    line = ed.get_text_line(y)
    if not line: return

    if not (0 <= x < len(line)) or not is_word_char(line[x]):
        msg_status('Caret not on word-char')
        return
        
    n1 = x
    n2 = x
    while n1>0 and is_word_char(line[n1-1]): n1-=1
    while n2<len(line)-1 and is_word_char(line[n2+1]): n2+=1
    x = n1
                                
    sub = line[n1:n2+1]
    if not is_word_alpha(sub):
        msg_status('Not text-word under caret')
        return
        
    print('Check word under caret: "%s"' % sub)
    if dict_obj.check(sub): return

    if with_dialog:
        ed.set_sel(ed.xy_pos(x, y), len(sub))
        rep = dlg_spell(sub)
        if rep is None: return
        if rep=='': return
        ed.replace(ed.xy_pos(x, y), len(sub), rep)
    else:
        ed.set_sel(ed.xy_pos(x, y), len(sub), True)
        ed.set_attr(ATTRIB_COLOR_BG, html_color_to_int(op_color_back))
        
    ed.set_caret_xy(x, y) 


def get_next_pos(offset, is_next):
    m = ed.get_attr()
    if not m: return
    #i[0]=range_start, i[1]=range_end
    m = [(i[0], i[1]) for i in m]
    if not m: return
    
    if is_next:
        m = [i for i in m if i[0]>offset]
        if m: return m[0]
    else:
        m = [i for i in m if i[1]<offset]
        if m: return m[len(m)-1]
       
    
def do_goto(is_next):
    offset = ed.get_caret_pos()
    m = get_next_pos(offset, is_next)
    if m:
        ed.set_caret_pos(m[0])
        msg_status('Go to misspelled')
    else:
        msg_status('Cannot go to next/prev')


#print('result:', dlg_spell('tst'))        

class Command:
    active = False

    def check(self):
        do_work()
    
    def check_suggest(self):
        do_work(True)
      
    def check_word(self):
        do_work_word(False)
    
    def check_word_suggest(self):
        do_work_word(True)
    
    def on_change_slow(self, ed_self):
        if self.active:
            do_work_if_name(ed_self)

    def toggle_hilite(self):
        self.active = not self.active
        if self.active:
            do_work_if_name(ed)
        else:
            ed.set_attr(ATTRIB_CLEAR_ALL, 0)
        
        text = 'Spell-check highlight: '+ ('on' if self.active else 'off')
        msg_status(text) 

    def select_dict(self):
        res = dlg_select_dict()
        if res is None: return
        global filename_ini
        global op_lang
        global dict_obj
        op_lang = res
        ini_write(filename_ini, 'op', 'lang', op_lang)
        dict_obj = enchant.Dict(op_lang)
        if self.active:
            do_work_if_name(ed)
            
    def edit_config(self):
        global op_lang
        global op_confirm_esc
        global op_file_types
        global op_color_back
        global filename_ini
        ini_write(filename_ini, 'op', 'lang', op_lang)
        ini_write(filename_ini, 'op', 'confirm_esc_key', op_confirm_esc)
        ini_write(filename_ini, 'op', 'file_extension_list', op_file_types)
        ini_write(filename_ini, 'op', 'color_back', op_color_back)
        if os.path.isfile(filename_ini):
            file_open(filename_ini)

    def goto_next(self):
        do_goto(True)
    def goto_prev(self):
        do_goto(False)
        
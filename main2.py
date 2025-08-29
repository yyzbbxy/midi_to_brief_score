
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QMainWindow
from PyQt5.QtCore import QFile, QTextStream, Qt
import mido
import numpy as np
import os
from input import Ui_input
import version_diary
import about
#主页面
class MyApp(QtWidgets.QMainWindow, Ui_input):
    def __init__(self):
        super().__init__()
        #ui_dir = os.path.join(os.getcwd(),"input.ui")
        #uic.loadUi(ui_dir, self)
        self.setupUi(self)

        
        self.note_ls = ["1","1#","2","2#","3","4","4#","5","5#","6","6#","7"]
        self.note_str_ls = ["G","G#","A","A#","B","C","C#","D","D#","E","F","F#"]
        self.jie_ls = ["2", "3", "4", "6"]
        self.pai_ls = ["4", "8"]
        self.note_text = 5
        self.note_height = 5
        self.jie = 2
        self.pai = 0
        self.data = None
        self.debug = True

        #设置控件
        self.btn_openfile = self.findChild(QtWidgets.QPushButton, "btn_openfile")
        self.btn_save = self.findChild(QtWidgets.QPushButton, "btn_save")
        self.text_edit = self.findChild(QtWidgets.QTextEdit, "text")
        self.cbox_note = self.findChild(QtWidgets.QComboBox, "cbox_note")
        self.cbox_height = self.findChild(QtWidgets.QComboBox, "cbox_height")
        self.cbox_jie = self.findChild(QtWidgets.QComboBox, "cbox_jie")
        self.cbox_pai = self.findChild(QtWidgets.QComboBox, "cbox_pai")
        self.version = self.findChild(QtWidgets.QAction, "version")
        self.about = self.findChild(QtWidgets.QAction, "about")
        self.menu_open_midi = self.findChild(QtWidgets.QAction, "menu_open_midi")
        self.menu_output_txt = self.findChild(QtWidgets.QAction, "menu_output_txt")
        self.txt_title = self.findChild(QtWidgets.QPlainTextEdit, "txt_title")
        self.txt_author = self.findChild(QtWidgets.QPlainTextEdit, "txt_author")

        #设置控件初值
        for i in self.note_str_ls:
            self.cbox_note.addItem(i)
        for i in range(12):
            self.cbox_height.addItem(str(i))
        for i in self.jie_ls:
            self.cbox_jie.addItem(i)
        for i in self.pai_ls:
            self.cbox_pai.addItem(i)
        self.cbox_note.setCurrentIndex(self.note_text)
        self.cbox_height.setCurrentIndex(self.note_height)
        self.cbox_jie.setCurrentIndex(self.jie)
        self.cbox_pai.setCurrentIndex(self.pai)
        self.title = "title"
        self.author = "author"
        self.txt_title.setPlainText(self.title)
        self.txt_author.setPlainText(self.author)


        #按钮链接函数
        self.btn_openfile.clicked.connect(self.input_data)
        self.btn_save.clicked.connect(self.save_file)
        self.cbox_note.currentIndexChanged.connect(self.change_note)
        self.cbox_height.currentIndexChanged.connect(self.change_height)
        self.cbox_jie.currentIndexChanged.connect(self.change_jie)
        self.cbox_pai.currentIndexChanged.connect(self.change_pai)
        self.version.triggered.connect(self.show_version)
        self.about.triggered.connect(self.show_about)
        self.menu_open_midi.triggered.connect(self.input_data)
        self.menu_output_txt.triggered.connect(self.save_file)
        self.txt_title.textChanged.connect(self.title_change)
        self.txt_author.textChanged.connect(self.author_change)

    #打开midi文件
    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File")
        if not file_name:
            print("文件不存在")
        elif not file_name.endswith(".mid"):
            print("文件不为midi")
        else:
            midi_file = mido.MidiFile(file_name)
            #轨道为空标志
            track_empty = True
            track_final = []
            track_temp = []
            #读取每个track
            self.beat = midi_file.ticks_per_beat
            if self.debug:
                print(midi_file.ticks_per_beat)
            '''
            file = open(file_name, "r", encoding="ISO8859-1")
            lines = file.readlines()
            for line in lines:
                print("y")
                print(line)
            '''
            for track in midi_file.tracks:
                #每个track里的事件
                #if self.debug:
                    #print(track)
                #记录metamessage积攒的时间
                meta_time = 0
                for msg in track:
                    print(msg)
                    #print(msg.type)
                    msg_bug_flag = False
                    if msg.type == "lyrics":
                        meta_time += msg.time
                        text = msg.text.encode('ISO-8859-1')
                        print(text)
                        text = text.decode('utf-8')
                        print(text)
                    if msg.type == "note_on" or msg.type == "note_off":
                        track_empty = False
                        #记录每个timestamp
                        if msg.type == "note_on":
                            if self.debug:
                                print("on",msg.note,msg.time,track_temp)
                            track_temp.append(msg.note)
                        else:
                            if self.debug:
                                print("off",msg.note,msg.time,track_temp)
                            #存在有off没on的未知情况
                            if msg.note in track_temp:
                                track_temp.remove(msg.note)
                            else:
                                msg_bug_flag = True
                        
                        if not msg_bug_flag:
                            if track_temp:
                                msg = [track_temp[-1], msg.time+meta_time]
                            else:
                                msg = ["null", msg.time+meta_time]
                            meta_time = 0
                            track_final.append(msg)
                if not track_empty:
                    return track_final
                    break
    
    #将最小精度音符转化为简谱代码
    def num_to_code(self,num,note):
        str_note = ""
        num_1_4 = num // 8
        count = 0
        if num_1_4 >1:
            count += 1
            str_note = str_note + str(note) + " "
            for i in range(num_1_4-1):
                if note == '0':
                    str_note += "0 "
                else:
                    str_note += "- "
        elif num_1_4 ==1:
            count += 1
            str_note += str_note + str(note) + " "
        
        temp = num % 8
        num_1_8 = temp // 4
        if num_1_8 != 0:
            count += 1
            str_note = str_note + str(note) + "/ "
        temp = temp % 4
        num_1_16 = temp // 2
        if num_1_16 != 0:
            count += 1
            str_note = str_note + str(note) + "// "
        temp = temp % 2
        num_1_32 = temp
        if num_1_32 != 0:
            count += 1
            str_note = str_note + str(note) + "/// "
        if count > 1 and note != "0":
            str_note = "(" + str_note + ")"
        return str_note

    #音高转文本
    def note_to_str(self,note):
        #C5为60
        if note == "null":
            return "0"
        else:
            note = note - (self.note_text-5) - (self.note_height-5) * 12
            note_str = ""
            if note>=60 and note<72:
                note_str = self.note_ls[note%12]
            elif note<60:
                note_str = note_str + self.note_ls[note%12]
                for i in range((60-note-1)//12+1):
                    note_str = note_str + ","
            else:
                note_str = note_str + self.note_ls[note%12]
                for i in range((note-60)//12):
                    note_str = note_str + "'"
            return note_str
    
    #每四小节换行
    def change_line(self,section_count):
        if section_count % 4 == 0:
            return "\nQ: "
        else:
            return ""

    #时间块划分
    def divide(self,blocks,num_clap,clap):
        #384为1音符，96为1/4音符,精度设置1/32音符即12
        #4/4拍为：1个1/4音符为一拍，4个1/4音符为1小节
        #一拍长度
        #beat = int(384 / clap)
        #1/32分音符长度
        note_32 = (self.beat * clap) // (8 * num_clap)
        #一节长度
        section = 4 * self.beat
        note = "Q: "
        section_count = 0
        for block in blocks:
            block[0] = self.note_to_str(block[0])
            #跨小节数量
            if block[2] % section ==0:
                section_num = block[2] // section - block[1] // section
                section_end_flag = True
            else:
                section_num = block[2] // section - block[1] // section + 1
                section_end_flag = False
            #单音块每小节划分长度
            
            if section_num == 1:
                min_num = (block[2] - block[1]) // note_32
                note = note + self.num_to_code(min_num,block[0])
            elif section_num == 2:
                min_num = ((block[1] // section + 1) * section - block[1]) // note_32
                if block[0] != "0":
                    note = note + "("
                note = note + self.num_to_code(min_num,block[0]) + "| "
                section_count += 1
                note += self.change_line(section_count)
                if block[2] % section == 0:
                    min_num = section // note_32
                else:
                    min_num = (block[2] - (block[2] // section) * section) // note_32
                note = note + self.num_to_code(min_num,block[0])
                if block[0] != "0":
                    note = note + ")"
            else:
                min_num = ((block[1] // section + 1) * section - block[1]) // note_32
                if block[0] != "0":
                    note = note + "("
                note = note + self.num_to_code(min_num,block[0]) + "| "
                section_count += 1
                note += self.change_line(section_count)
                for i in range(section_num-2):
                    note = note + self.num_to_code(section // note_32,block[0]) + "| "
                    section_count += 1
                    note += self.change_line(section_count)
                if block[2] % section == 0:
                    min_num = 32
                else:
                    min_num = (block[2] - (block[2] // section) * section) // note_32
                note = note + self.num_to_code(min_num,block[0])
                if block[0] != "0":
                    note = note + ")"
            #添加小节结束标志
            if section_end_flag:
                note = note + ("| ")
                section_count += 1
                note += self.change_line(section_count)
        return note

    #整理数据
    def data_analyze(self,data):
        #记录时间块
        block = []
        block_s = 0
        block_e = 0
        if self.debug:
            print(data)
        #初始休止符midi未记录情况
        if data[0][1] != 0:
            block.append(["null",0,data[0][1]])
            block_e = data[0][1]
        #按起止时间定义时间块
        for i in range(len(data)-1):
            #去除连续部分冗余信息
            if data[i+1][1] != 0:
                block_s =block_e
                block_e = data[i+1][1] + block_s
                block.append([data[i][0],block_s,block_e])
        #4/4拍划分
        output = self.divide(block, int(self.jie_ls[self.jie]), int(self.pai_ls[self.pai]))
        return output

    #抬头
    def info(self):
        title = "B: " + self.title + "\n"
        writer = "Z: " + self.author + "\n"
        note = "D: " + self.note_str_ls[self.note_text] + "\n"
        beat = "P: " + str(self.jie_ls[self.jie]) + "/" + str(self.pai_ls[self.pai]) + "\n"
        whole_title = title + writer + note + beat
        return whole_title

    #展示窗口
    def show_text(self):
        if self.data:
            output = self.info() + self.data_analyze(self.data)
            print(output)
            self.text_edit.setPlainText(output)
        else:
            print("文件为空")

    #导入文件
    def input_data(self):
        self.data = self.open_file()
        self.show_text()
        
    #更改标题
    def title_change(self):
        self.title = self.txt_title.toPlainText()
        self.show_text()

    #更改作者
    def author_change(self):
        self.author = self.txt_author.toPlainText()
        self.show_text()

    #更改初始note
    def change_note(self):
        self.note_text = self.cbox_note.currentIndex()
        print(self.note_text)
        self.show_text()
    
    #更改初始height
    def change_height(self):
        self.note_height = int(self.cbox_height.currentText())
        print(self.note_height)
        self.show_text()

    #更改初始一小节长度长度，如4个1/4音符为1小节
    def change_jie(self):
        self.jie = self.cbox_jie.currentIndex()
        print(self.jie)
        self.show_text()
        
    #更改初始一拍长度，如1个1/4音符为一拍
    def change_pai(self):
        self.pai = self.cbox_pai.currentIndex()
        print(self.pai)
        self.show_text()

    #保存txt文件
    def save_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File","","Text Files (*.txt)")
        if file_name:
            file = QFile(file_name)
            if file.open(QFile.WriteOnly | QFile.Text):
                stream = QTextStream(file)
                text = self.text_edit.toPlainText()
                stream << text
                file.close()

    def show_version(self):
        self.version_ui = Version()
        self.version_ui.show()
        
    def show_about(self):
        self.about_ui = About()
        self.about_ui.show()

class Version(QtWidgets.QDialog, version_diary.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.retranslateUi(self)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint);
        
class About(QtWidgets.QDialog, about.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.retranslateUi(self)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint);

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QFile, QTextStream
import mido
import numpy as np
import os

#主页面
class MyApp(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        ui_dir = os.path.join(os.getcwd(),"input.ui")
        uic.loadUi(ui_dir, self)

        #设置控件
        self.btn_openfile = self.findChild(QtWidgets.QPushButton, "btn_openfile")
        self.btn_save = self.findChild(QtWidgets.QPushButton, "btn_save")
        self.text_edit = self.findChild(QtWidgets.QTextEdit, "text")

        #按钮链接函数
        self.btn_openfile.clicked.connect(self.show_data)
        self.btn_save.clicked.connect(self.save_file)

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
            for track in midi_file.tracks:
                #每个track里的事件
                for msg in track:
                    if msg.type == "note_on" or msg.type == "note_off":
                        track_empty = False
                        #记录每个timestamp
                        if msg.type == "note_on":
                            track_temp.append(msg.note)
                        else:
                            track_temp.remove(msg.note)
                        if track_temp:
                            msg = [track_temp[-1], msg.time]
                        else:
                            msg = ["null", msg.time]
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
        note_ls = ["1","1#","2","2#","3","4","4#","5","5#","6","6#","7"]
        if note == "null":
            return "0"
        else:
            note_str = ""
            if note>=60 and note<72:
                note_str = note_ls[note%12]
            elif note<60:
                note_str = note_str + note_ls[note%12]
                for i in range((60-note-1)//12+1):
                    note_str = note_str + ","
            else:
                note_str = note_str + note_ls[note%12]
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
        beat = int(384 / clap)
        #一节长度
        section = num_clap * beat
        note = "Q: "
        section_count = 0
        for block in blocks:
            print(section_count)
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
                min_num = (block[2] - block[1]) // 12
                note = note + self.num_to_code(min_num,block[0])
            elif section_num == 2:
                min_num = ((block[1] // section + 1) * section - block[1]) // 12
                note = note + "(" + self.num_to_code(min_num,block[0]) + "| "
                section_count += 1
                note += self.change_line(section_count)
                min_num = (block[2] - (block[2] // section) * section) // 12
                note = note + self.num_to_code(min_num,block[0]) + ")"
            else:
                min_num = ((block[1] // section + 1) * section - block[1]) // 12
                note = note + "(" + self.num_to_code(min_num,block[0]) + "| "
                section_count += 1
                note += self.change_line(section_count)
                for i in range(section_num-2):
                    note = note + self.num_to_code(32,block[0]) + "| "
                    section_count += 1
                    note += self.change_line(section_count)
                min_num = (block[2] - (block[2] // section) * section) // 12
                note = note + self.num_to_code(min_num,block[0]) + ")"
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
        #初始休止符midi未记录情况
        if data[0][1] != 0:
            block.append(["null",0,data[0][1]])
            block_e = data[0][1]
        #按起止时间定义时间块
        for i in range(len(data)-1):
            #去除连续部分冗余信息
            if data[i][0] != "null" or data[i+1][1] != 0:
                block_s =block_e
                block_e = data[i+1][1] + block_s
                block.append([data[i][0],block_s,block_e])
        #4/4拍划分
        output = self.divide(block,4,4)
        return output

    #抬头
    def title(self):
        title = "B: demo\n"
        writer = "Z: writer\n"
        note = "D: C\n"
        beat = "P:4/4\n"
        whole_title = title + writer + note + beat
        return whole_title

    #展示窗口
    def show_data(self):
        data = self.open_file()
        if data:
            output = self.title() + self.data_analyze(data)
            print(output)
            self.text_edit.setPlainText(output)
        else:
            print("文件为空")
    
    #保存txt文件
    def save_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File","","Text Files (*.txt)")
        if file_name:
            file = QFile(file_name)
            print(file_name)
            if file.open(QFile.WriteOnly | QFile.Text):
                stream = QTextStream(file)
                text = self.text_edit.toPlainText()
                stream << text
                file.close()



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
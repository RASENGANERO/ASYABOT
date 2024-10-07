from selenium import webdriver
import time
import random
import os
import pickle
import requests
import sys
from PyQt5 import Qt
from PyQt5.QtWidgets import (QWidget,QMessageBox,QGridLayout,QApplication,QPushButton,QTableWidgetItem,QTableWidget,QHeaderView,
							 QSizePolicy,QAbstractItemView,QTextEdit,QInputDialog,QFileDialog,QMenu,QAction)
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import *
import sqlite3
SCROLLS=5

class DataBaseEdited:
	@staticmethod
	def insert_to_database(curs,datas):
		datas=["'"+str(a)+"'" for a in datas]
		sql=','.join(datas)
		sqlite_insert_query = """INSERT INTO instagram(urls, publications,subscribers,followers) VALUES("""+sql+""");"""
		curs.execute(sqlite_insert_query)
		
	@staticmethod
	def delete_from_database(curs,datas):
		sql="'"+str(datas)+"'"
		sqlite_insert_query = """DELETE FROM instagram WHERE urls="""+sql+""";"""
		curs.execute(sqlite_insert_query)

	@staticmethod
	def check_unique(curs,datas):
		datas="'"+str(datas).replace('"','').replace("'",'').replace('@','')+"'"
		try:
			curs.execute("""SELECT *FROM instagram WHERE urls="""+datas+""";""")
			x=curs.fetchall()
		except Exception:
			return 1
			pass
		if len(x)!=0:
			return 1
		else:
			return 0


class DataBase(QThread):
	dataemited=pyqtSignal(list)
	def __init__(self,changesql,curs):
		super().__init__()
		self.changesql=changesql
		self.curs=curs

	def run(self):
		sqlite_insert_query=None
		if self.changesql==1:
			sqlite_insert_query = """SELECT *FROM instagram WHERE id>0;"""
		if self.changesql==2:
			sqlite_insert_query = """SELECT *FROM instagram ORDER BY publications ASC;"""
		if self.changesql==3:
			sqlite_insert_query = """SELECT *FROM instagram ORDER BY subscribers ASC;"""
		if self.changesql==4:
			sqlite_insert_query = """SELECT *FROM instagram ORDER BY followers ASC;"""
		self.curs.execute(sqlite_insert_query)
		query=self.curs.fetchall()
		query=[list(a)[1::] for a in query]
		for v in range(len(query)):
			self.dataemited.emit(query[v])


DRIVER='geckodriver.exe'
class Driver:
	@staticmethod
	def start():
		option=webdriver.FirefoxOptions()
		option.set_preference("dom.webdriver.enabled", False)
		drivers=webdriver.Firefox(None,None,None,None,None,DRIVER,option)
		drivers.get('https://www.instagram.com/')
		return drivers

	@staticmethod
	def exit(dr):
		dr.delete_all_cookies()
		dr.close()
		dr.quit()
		time.sleep(2)


class GetSubscribers(QThread):
	users_signal=pyqtSignal(bool,list)
	def __init__(self,file,url):
		super().__init__()
		self.cookie=file
		self.url_user=url

	def run(self):

		self.driver=Driver.start()
		cookies=pickle.load(open(str(self.cookie),'rb'))
		for cook in cookies:
			self.driver.add_cookie(cook)
		self.driver.get('https://www.instagram.com/')
		time.sleep(3)

		for pkrs in range(len(self.url_user)):
			self.driver.get(self.url_user[pkrs])
			time.sleep(3)
			
			self.driver.implicitly_wait(30)
			followers_button = self.driver.find_element_by_css_selector("li.Y8-fY:nth-child(2) > a:nth-child(1) > div:nth-child(1)")




			followers_count = self.driver.execute_script("""var q;
															var a= document.getElementsByTagName('span');
															for (var i=0;i<a.length;i++){
															if (a[i].getAttribute('title')!=null){
															q=a[i].getAttribute('title');}
															}
															return q;""")
			
			followers_count=int(str(followers_count).replace(' ','').strip())
			self.users_signal.emit(False,['Количество подписчиков со страницы: '+str(followers_count)])		
			loops_count = int(followers_count / 12)
			self.driver.execute_script("""var a= document.getElementsByTagName('a');
										  for (var i=0; i<a.length; i++){
										  if (a[i].getAttribute('href').endsWith('followers/')==true){
										  a[i].click();
										  }
										  }""")
			#self.driver.implicitly_wait(30)
			#self.driver.find_element_by_xpath("/html/body/div[1]/section/main/div/header/section/ul/li[2]/a/span").click()
			time.sleep(6)
			cookies = self.driver.get_cookies()
			info = requests.Session()
			for cookie in cookies:
				info.cookies.set(cookie['name'], cookie['value'])
			followers_urls = []

			i=int(0)
			while i<=followers_count:
				for scroll in range(0,SCROLLS):
					self.driver.execute_script("""var fDialog = document.querySelector('div[role="dialog"] .isgrP');
												fDialog.scrollTop = fDialog.scrollHeight;""")
					time.sleep(0.2)
				time.sleep(5)
				follower=self.driver.execute_script("""return document.querySelector('.isgrP').innerText;""")
				follower=str(follower).split('\n')

				if 'Рекомендации для вас' in follower:
					del follower[follower.index('Рекомендации для вас'):]

				#vr_in_user=[]
				#for q in range(len(follower)):
				#	if str(follower[q])=='Подписки':
				#		vr_in_user.append(str(follower[q]))
				#		vr_in_user.append(str(follower[q-1]))
				#		vr_in_user.append(str(follower[q-2]))

				#if len(vr_in_user)!=0:
				#	for q in range(len(vr_in_user)):
				#		follower=[a for a in follower if str(a)!=vr_in_user[q]]


				follower=[a for a in follower if str(a)!='Подписаться']
				follower=follower[::2]
				follower=['https://www.instagram.com/'+str(a)+'/' for a in follower]

				for v in range(len(follower)):
					if str(follower[v]) not in followers_urls:
						followers_urls.append(str(follower[v]))
						self.users_signal.emit(False,['Найден подписчик: '+str(follower[v]).split('/')[-1]+'  '+str(len(followers_urls))+' из '+str(followers_count)+' страница: '+str(pkrs+1)+' из '+str(len(self.url_user))])
						try:

							inf_akk=info.get(str(follower[v]+'?__a=1')).json()
						except Exception:
							inf_akk={}
							
						if 'graphql' in inf_akk:
							self.users_signal.emit(True,[str(follower[v]),str(int(inf_akk['graphql']['user']['edge_owner_to_timeline_media']['count'])+int(inf_akk['graphql']['user']['edge_felix_video_timeline']['count'])),str(inf_akk['graphql']['user']['edge_followed_by']['count']),str(inf_akk['graphql']['user']['edge_follow']['count'])])
						else:
							self.users_signal.emit(True,[str(follower[v]),'Неизвестно','Неизвестно','Неизвестно'])
				
				i=len(followers_urls)
				
			info.close()
			
		Driver.exit(self.driver)


class SetSubscribers(QThread):
	set_pod=pyqtSignal(str)
	def __init__(self,file,follow):
		super().__init__()
		self.cookie=file
		self.user_follow=follow

	def run(self):
		
		self.driver=Driver.start()
		cookies=pickle.load(open(str(self.cookie),'rb'))
		for cook in cookies:
			self.driver.add_cookie(cook)
		self.driver.get('https://www.instagram.com/')
		time.sleep(3)
		
		for v in range(len(self.user_follow)):
			self.driver.get(str(self.user_follow[v]))
			check=self.driver.execute_script("""var col=0;
									var a=document.getElementsByTagName('button');
									for (let i=0;i<a.length;i++){
										if (a[i].innerText=='Подписаться'){
										col++;
										}
									}
									return col;""")
			if check==0:
				self.set_pod.emit('Вы подписаны на данный аккаунт!')
			else:
				self.driver.execute_script("""var a=document.getElementsByTagName('button');
					for (let i=0;i<a.length;i++){
					if (a[i].innerText=='Подписаться'){
						a[i].click();
					}
					}""")
				self.set_pod.emit('Вы подписались на аккаунт '+str(self.driver.current_url)+' '+str(v+1)+' из '+str(len(self.user_follow))+' Он будет удалён из базы!')
			time.sleep(random.randint(5,7))
		Driver.exit(self.driver)



class InstagramAuth(QThread):
	def __init__(self, filename):
		super().__init__()
		self.file = filename

	def run(self):		
		self.driver=Driver.start()
		time.sleep(120)
		pickle.dump(self.driver.get_cookies(),open(self.file,'wb'))
		Driver.exit(self.driver)



class ASYAGUI(QWidget):
	def __init__(self,*args):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.grid=QGridLayout()
		self.table=QTableWidget()
		self.setWindowTitle('Ася')
		self.create_table()
		self.but1=QPushButton('Куки для подписок')
		self.but2=QPushButton('Подписаться на пользователей')
		self.but3=QPushButton('Куки для подписчиков')
		self.but4=QPushButton('Получить подписчиков')
		self.texted=QTextEdit()
		self.texted.setReadOnly(True)
		

		self.but1.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)
		self.but2.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)
		self.but3.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)
		self.but4.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)
		self.grid.addWidget(self.but1,0,0)
		self.grid.addWidget(self.but2,1,0)
		self.grid.addWidget(self.but3,2,0)
		self.grid.addWidget(self.but4,3,0)		
		self.grid.addWidget(self.table,0,1,4,1)		
		self.grid.addWidget(self.texted,4,0,1,2)	
		
		self.but1.clicked.connect(self.auth_one)
		self.but2.clicked.connect(self.start_podpis)
		self.but3.clicked.connect(self.auth_two)
		self.but4.clicked.connect(self.get_podpis)

		self.menu_for_tabled=QMenu()
		self.act1=QAction('Отсортировать по публикациям')
		self.act2=QAction('Отсортировать по подписчикам')
		self.act3=QAction('Отсортировать по подпискам')
		self.act4=QAction('Удалить данные')
		self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.table.customContextMenuRequested[QtCore.QPoint].connect(self.menu_for_table)
		self.menu_for_tabled.addActions([self.act1,self.act2,self.act3,self.act4])
		self.act1.triggered.connect(self.sort_1)
		self.act2.triggered.connect(self.sort_2)
		self.act3.triggered.connect(self.sort_3)
		self.act4.triggered.connect(self.del_from_table)

		self.connection=sqlite3.connect('asya.db',check_same_thread=False,isolation_level=None)
		self.cursor=self.connection.cursor()

		self.set_tabled(1,'Данные из таблицы получены!')
		self.setLayout(self.grid)		
		self.setGeometry(250,250,1250,550)
		self.show()




	def menu_for_table(self,pos):
		self.menu_for_tabled.popup(QCursor.pos())

	def sort_1(self):
		self.set_tabled(2,'Таблица отсортирована по публикациям!')

	def sort_2(self):
		self.set_tabled(3,'Таблица отсортирована по подписчикам!')

	def sort_3(self):
		self.set_tabled(4,'Таблица отсортирована по подпискам!')




	def del_from_table(self):
		index_for_table=list()
		for ind in self.table.selectionModel().selectedRows():
			indexed=QtCore.QPersistentModelIndex(ind)
			index_for_table.append(indexed)
		if len(index_for_table)==0:
			QMessageBox.information(self,"Внимание!","Ни одна строка не выбрана!")
		else:
			for idx in index_for_table:
				item=str(self.table.item(idx.row(),0).text())
				self.removeRow(idx.row())
				DataBaseEdited.delete_from_database(self.cursor,str(item))
			self.connection.commit()




	def set_tabled(self,s,named):
		self.states_tbl=named
		self.table.setRowCount(0)
		self.set_tb = DataBase(s,self.cursor)
		self.set_tb.finished.connect(self.set_tb_finish)
		self.set_tb.dataemited.connect(self.set_tbl)
		self.set_tb.start()

	def set_tbl(self,var):
		if len(var)!=0:
			self.add_table(var)
	
	def set_tb_finish(self):
		QMessageBox.information(self,'Внимание!',self.states_tbl)
		del self.set_tb
		self.connection.commit()


	def add_table(self,varsed):
		self.table.insertRow(self.table.rowCount())
		self.table.scrollToBottom()
		for v in range(len(varsed)):
			item=QTableWidgetItem(str(varsed[v]))
			item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)
			self.table.setItem(self.table.rowCount()-1,v,item)
		self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)



	def auth_one(self):
		self.auth('Куки для подписок созданы!','1.pkl')

	def auth_two(self):
		self.auth('Куки для получения подписчиков созданы!','2.pkl')

	def auth(self,s,file):
		self.state=s
		self.instauth = InstagramAuth(file)
		self.instauth.finished.connect(self.auth_finish)
		self.instauth.start()



	def auth_finish(self):
		QMessageBox.information(self,'Внимание!',self.state)
		del self.instauth


	def get_podpis(self):		
		self.texted.clear()
		msgbox=QMessageBox()
		msgbox.setWindowTitle("Внимание!")
		msgbox.setText('Выберите действие')
		msgbox.addButton('Ввести ссылку на страницу', QMessageBox.YesRole)
		msgbox.addButton('Считать ссылки из файла', QMessageBox.YesRole)
		msgbox.addButton('Отмена', QMessageBox.YesRole)
		s=[]
		bttn = msgbox.exec_()

		if bttn == 0:
			sq,ok=QInputDialog.getText(self, 'Пожалуйста','Введите ссылку на страницу:')#.getText()
			if sq=='':
				QMessageBox.information(self,'Внимание!','Вы не указали ссылку!!!')
			else:
				if str(sq).startswith('https://www.instagram.com/')!=True and str(sq).endswith('/')!=True:
					QMessageBox.information(self,'Внимание!','Ваша ссылка не корректна!!!')
				else:
					s.append(str(sq))
					
		if bttn == 1:
			save_tb=str(QFileDialog().getOpenFileName(self,"Открыть файл данных",QDir().currentPath(),"All Files (*.txt)")[0])
			if len(save_tb)==0:
				QMessageBox.information(self,"Внимание!","Файл не выбран!")
			else:
				f=open(save_tb,'r')
				s=f.read().splitlines()
				f.close()
		if bttn == 2:
			QMessageBox.information(self,'Внимание!','Вы отменили сбор подписчиков!')
		if len(s)!=0:
			self.get_pod = GetSubscribers('2.pkl',s)
			self.get_pod.finished.connect(self.get_pod_finish)
			self.get_pod.users_signal.connect(self.get_users)
			self.get_pod.start()



	def get_pod_finish(self):
		QMessageBox.information(self,'Внимание!','Все подписчики получены!')
		self.texted.clear()
		del self.get_pod
		self.connection.commit()




	

		


	def get_users(self,var1,var2):
		if var1==False:
			self.texted.append(str(var2[0]))
		else:
			if DataBaseEdited.check_unique(self.cursor,var2[0])==1:
				self.texted.append('Подписчик '+var2[0]+' уже есть в базе!')
			else:
				if str(var2[0]).endswith('Подписки/')==True:
					self.texted.append('Подписчик '+var2[0]+' не будет добавлен в базу. Вы уже подписаны на него!')
				else:
					try:
						
						DataBaseEdited.insert_to_database(self.cursor,var2)
						self.texted.append('Подписчик '+var2[0]+' будет добавлен в базу.')
						self.add_table(var2)
					except Exception:
						self.texted.append('У подписчика нестандартная страница! Он не будет добавлен в базу!')
				




	def start_podpis(self):
		self.texted.clear()
		lk=[]
		r=int(15)
		if self.table.rowCount()<15:r=self.table.rowCount()
		for v in range(0,r):
			lk.append(str(self.table.item(v,0).text()))
		self.set_pod = SetSubscribers('1.pkl',lk)
		self.set_pod.finished.connect(self.set_pod_finish)
		self.set_pod.set_pod.connect(self.set_users)
		self.set_pod.start()
		


	def set_users(self,var1):
		self.texted.append(str(var1))
		DataBaseEdited.delete_from_database(self.cursor,str(self.table.item(0,0).text()))
		self.table.removeRow(0)


	def set_pod_finish(self):
		QMessageBox.information(self,'Внимание!','Вы подписались на всех подписчиков!')
		del self.set_pod
		self.connection.commit()


	def create_table(self):
		self.table.setColumnCount(4)
		self.table.setHorizontalHeaderLabels(['Страница','Публикации','Подписчики','Подписки'])
		self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.table.verticalHeader().setVisible(False)
		self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
		


	def closeEvent(self, event):
		close=QMessageBox.question(self,'Внимание!','Вы хотите выйти из программы?',QMessageBox.Ok|QMessageBox.No)
		if close==QMessageBox.Ok:
			event.accept()
			self.cursor.close()
			self.connection.close()
		else:
			event.ignore()


if __name__=='__main__':
    app=QApplication(sys.argv)
    exe=ASYAGUI()
    sys.exit(app.exec_())



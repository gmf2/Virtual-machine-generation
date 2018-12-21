#!/usr/bin/python  
# -*- coding: utf-8 -*-   

import os
import sys

from copy import deepcopy
from lxml import etree


#Crea las maquinas, lb y c1 fijas y Sx depende del parametro introducido despues
#	python pfinalp1 create 
def create(n):
	#Maquinas virtuales
	#numero de servidores variable n
	servidores={}
	for i in range(1,n+1):
		servidores[i]=os.system('qemu-img create -f qcow2 -b /home/ce/p3/plantilla/cdps-vm-base-p3.qcow2 s%d.qcow2' %i)
	#balanceador y cliente
	os.system('qemu-img create -f qcow2 -b /home/ce/p3/plantilla/cdps-vm-base-p3.qcow2 lb.qcow2')
	os.system('qemu-img create -f qcow2 -b /home/ce/p3/plantilla/cdps-vm-base-p3.qcow2 c1.qcow2')
	#creo las plantillas	
	#lb
	os.system('cp /home/ce/p3/plantilla/plantilla-vm-p3.xml lb.xml')
	#MODIFICAR FICHERO	
	xml('lb.xml')
	#c1
	os.system('cp /home/ce/p3/plantilla/plantilla-vm-p3.xml c1.xml')
	#MODIFICAR FICHERO	
	xml('c1.xml')

	#servidores
	for a in range(1, n+1):
		os.system('cp /home/ce/p3/plantilla/plantilla-vm-p3.xml s%d.xml' %a)
		xmlsx('s%d.xml' %a)
		#MODIFICAR FICHERO	os.system('vi s%d.xml' %a)
	
	#Bridges de las dos redes
	os.system('sudo brctl addbr LAN1')
	os.system('sudo brctl addbr LAN2')
	os.system('sudo ifconfig LAN1 up')
	os.system('sudo ifconfig LAN2 up')


#Realiciza toda la operacion de cambio sobre los archivo de xml, reescribe y guarda
	
def xml(fich):
	#buscar y cargar el fichero
	tree = etree.parse(fiche)
	nombre= fich
	#NODO raiz
	root = tree.getroot()
	name = root.find("name")
	fich.text = nombre 
	#cambiamos las XXX 
	ddsource= root.find("./devices/disk[@type='file']/source")
	ddsource.set("file","/home/ce/p3/%s.qcow2" %nombre) # path donde estan las imagenes creadas (.qcow2)
	#bridge LAN1 para lb y c1
	infsource=root.find("./devices/interface[@type='bridge']/source")
	infsource.set("bridge","LAN1") #Bridge LAN1 en lb y c1
	if (nombre=="lb"):	#Creo la interfaz para la LAN2 solo en lb
		devices=root.find('devices')
		interface=devices.find('interface')
		interfaceLAN2=deepcopy(interface)	#Copio interfaz para añadir LAN2
		interfaceLAN2.find('source').set("bridge","LAN2")
		devices.append(interfaceLAN2) #Añadida al xml
	fichero = open("%s.xml" %nombre, 'w') 
	fichero.write(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8"))
	fichero.close() # xml cerrado
def xmlsx(sx):
	#buscar y cargar el fichero
	tree = etree.parse(sx)
	nombre= sx
	#NODO raiz
	root = tree.getroot()
	sx = root.find("name")
	sx.text = nombre 
	#cambiamos las XXX 
	ddsource= root.find("./devices/disk[@type='file']/source")
	ddsource.set("file","/home/ce/p3/%s.qcow2" %nombre) # path donde estan las imagenes creadas (.qcow2)
	#bridge LAN1 para lb y c1
	#bridge LAN2 para los servers
	infsource=root.find("./devices/interface[@type='bridge']/source")
	infsource.set("bridge","LAN2")
	fichero = open("%s.xml" %nombre, 'w')
	fichero.write(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8")) 
	fichero.close() #cerrado


#Arranca las maquinas 
#	python pfinalp2 start	
def start():
	#arranque gestor de maq V si hay fallo o en el lab: 	os.system('HOME=/mnt/tmp sudo virt-manager')
	os.system('sudo virt-manager')
	#servidores
	serN=contarxml()-2 #restas lb y c1
	for a in range(1, serN+1):
		print 'valores de numero de server: %d' %a
		os.system('sudo virsh create s%d.xml' %a)
		os.system('xterm -rv -sb -rightbar -fa monospace -fs 10 -title "s%d" -e "sudo virsh console s%d"&' %(a,a))
	#lb
	os.system('sudo virsh create lb.xml')
	os.system('xterm -rv -sb -rightbar -fa monospace -fs 10 -title "lb" -e "sudo virsh console lb"&')
	#cliente 1
	os.system('sudo virsh create c1.xml')
	os.system('xterm -rv -sb -rightbar -fa monospace -fs 10 -title "c1" -e "sudo virsh console c1"&')

#Para las maquinas
#	python pfinalp2 stop	
def stop():
	#servidores
	serN=contarxml()-2 #restas lb y c1
	for e in range (1,serN+1):
		os.system('sudo virsh shutdown s%d' %e)
	#lb
	os.system('sudo virsh shutdown lb')
	#cliente 1
	os.system('sudo virsh shutdown c1')	

#Borra todo lo que habiamos creado, las maquinas, los archivos y los puentes
#	python pfinalp2 destroy	
def destroy():
	#lb
	print ('destroy lb valor es igual a %d' %contarxml())
	os.system('rm -f lb.*')
	#cliente 1
	print ('destroy c1 valor es igual a %d' %contarxml())
	os.system('rm -f c1.*')			
	print ("Se han eliminado lb y c1")

	#servidores
	serN=contarxml() #restas lb y c1
	print ('destroy lb valor es igual a %d (lb -2)' %contarxml())
	for e in range (1,serN+2):
		os.system('rm -f s%d.*' %e) #borra todos los servidores
		print ('SERN valor es igual a %d' %serN)

	#borrar los bridges
	os.system('sudo ifconfig LAN1 down')
	os.system('sudo brctl delbr LAN1')
	os.system('sudo ifconfig LAN2 down')
	os.system('sudo brctl delbr LAN2')

	print ("Se han eliminado todos los servidores")
	
#Busca los archivos .xml en el directorio de la practica y los cuenta
def contarxml():
	c =0
	path= '.'
	listD= os.listdir(path)
	for fichero in listD:
			(nombre, extension) = os.path.splitext(fichero)
			if(extension =='.xml'): # or extension =='.qcow2'):
				c+=1
	print ('c valor es igual a %d' %c)
	return c

#MAIN: 	
try:
	tipo = sys.argv[1]
	
	if tipo== "create":
		nume = int(input("Numero de servidores: "))	
		if nume<1 or nume > 5:
			print "Debe introducir un número entre 1 y 5 ej. create 2"
		else:
			create(nume)
	elif tipo == "start":
		if contarxml() <1:
			print 'debe ejecutar antes Create'
		else:
			start()
	elif tipo == "stop":
		if contarxml() <1:
			print "debe ejecutar antes Create"
		else:
			stop()
	elif tipo == "destroy":
		destroy()
	else:
		print "Esa orden no existe, create x ; start ; stop ; destroy"

except KeyboardInterrupt:
	print('\n\nKeyboard exception received. Exiting.')
	exit()

except ValueError:

        print "Mal introducido"
	print"Añada un parametro, mala ejecucion"

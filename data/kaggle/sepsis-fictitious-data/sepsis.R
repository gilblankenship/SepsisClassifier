## ANÁLISIS ESTADÍSTICO DESCRIPTIVO E INFERENCIAL MEDIANTE R DE UN CONJUNTO DE DATOS FICTICIOS SOBRE SEPSIS EN UNIDAD DE CUIDADOS INTENSIVOS
## Diego Fernando Scarpetta Gonzalez, MD; Henry Bedoya Gonzalez, MD y Bibiana Perez Hernandez, PhD


#1.Definir carpeta de trabajo
getwd()  #Devuelve la ruta del directorio de trabajo actual
setwd("D://MIB//INVESTIGACIÓN")

#2.Instalar las Librer?as 

install.packages("readr")     
install.packages("readxl")     
install.packages("latticeExtra")
install.packages ("Hmisc") 
install.packages ("ggplot2")
install.packages ("carData")
install.packages ("tidyverse")
install.packages ("plyr")
install.packages ("Publish")
install.packages("car")

#3.Cargar el archivo de trabajo
library(readr)  
sepsis<-read.csv(file ="D:/MIB/INVESTIGACIÓN/sepsis_def.csv", header=T)
sepsis
View(sepsis)



#4.Exploracion del contenido de los datos
str(sepsis)           #estructura
dim(sepsis)           #dimension
names(sepsis)         #nombre de las variables
head(sepsis)          #primeros elementos
tail(sepsis)          #encabezado ?ltimos elementos
summary(sepsis)       #resumen del contenido de las variables
any(is.na(sepsis))    #presencia de missings
mean(sepsis$Wbc_inicial,na.rm = TRUE)
nrow(sepsis)          #numero de filas
ncol(sepsis)
nrow(na.omit(sepsis)) #selecciona solo las filas con informacion

# Nombrar variables categoricas 

summary(sepsis)

sepsis$Sexo <- factor(sepsis$Sexo)
sepsis$Hospital <- factor(sepsis$Hospital)
sepsis$Proced <- factor(sepsis$Proced)
sepsis$Reg_salud <- factor(sepsis$Reg_salud)
sepsis$HTA <- factor(sepsis$HTA)
sepsis$ARA_2<- factor(sepsis$ARA_2)
sepsis$IECA<- factor(sepsis$IECA)
sepsis$Tiazidas<- factor(sepsis$Tiazidas)
sepsis$diur_asa<- factor(sepsis$diur_asa)
sepsis$Calcio.antagonista<- factor(sepsis$Calcio.antagonista)
sepsis$Beta_bloqueador<- factor(sepsis$Beta_bloqueador)
sepsis$Otros_antihta<- factor(sepsis$Otros_antihta)
sepsis$DM_2<- factor(sepsis$DM_2)
sepsis$Metformina<- factor(sepsis$Metformina)
sepsis$iSGLT2<- factor(sepsis$iSGLT2)
sepsis$DDPIV<- factor(sepsis$DDPIV)
sepsis$GLP1a<- factor(sepsis$GLP1a)
sepsis$Insulina_basal<- factor(sepsis$Insulina_basal)
sepsis$Insulina_preprandial<- factor(sepsis$Insulina_preprandial)
sepsis$Otros_antidiabeticos<- factor(sepsis$Otros_antidiabeticos)
sepsis$Hipotiroidismo<- factor(sepsis$Hipotiroidismo)
sepsis$ERC<- factor(sepsis$ERC)
sepsis$Tabaco<- factor(sepsis$Tabaco)
sepsis$Enf_coronaria<- factor(sepsis$Enf_coronaria)
sepsis$Obesidad<- factor(sepsis$Obesidad)
sepsis$Dislipidemia<- factor(sepsis$Dislipidemia)
sepsis$ACV<- factor(sepsis$ACV)
sepsis$Fib_aur<- factor(sepsis$Fib_aur)
sepsis$Autoinmune<- factor(sepsis$Autoinmune)
sepsis$Sepsis<- factor(sepsis$Sepsis)
sepsis$Alt_C<- factor(sepsis$Alt_C)
sepsis$Norepi<- factor(sepsis$Norepi)
sepsis$Vasopresina<- factor(sepsis$Vasopresina)
sepsis$ATB_1<- factor(sepsis$ATB_1)
sepsis$ATB_2<- factor(sepsis$ATB_2)
sepsis$ATB_3<- factor(sepsis$ATB_3)
sepsis$Cultivos<- factor(sepsis$Cultivos)
sepsis$IOT<- factor(sepsis$IOT)
sepsis$IRA<- factor(sepsis$IRA)
sepsis$Dialisis<- factor(sepsis$Dialisis)
sepsis$Muerte<- factor(sepsis$Muerte)

# Función para preguntar si una variable es categorica

is.factor(sepsis$Muerte)  # esta si
is.factor(sepsis$Norepi_0)  # esta no 

# Colocar etiquetas a los valores numericos de las variables categoricas

levels(sepsis$Sexo) <- c("Hombre","Mujer")
levels(sepsis$Hospital) <- c("Farallones","León XIII")
levels(sepsis$Proced) <- c("Bello","Caldas","Cali","Envigado","Medellin","Pasto","Popayan","Quibdo","S_Quilichao","Tumaco","Urrao","Yarumal")
levels(sepsis$Reg_salud) <- c("Subsidiado","Contributivo")

library(car) 
#levels(sepsis$HTA) <- c("no","si")
sepsis$HTA2<- recode(sepsis$HTA,"0='2'; 1='1'")
levels(sepsis$HTA2) <- c("si", "no")
levels(sepsis$ARA_2) <- c("no","si")
levels(sepsis$IECA) <- c("no","si")
levels(sepsis$Tiazidas) <- c("no","si")
levels(sepsis$diur_asa) <- c("no","si")
levels(sepsis$Calcio.antagonista) <- c("no","si")
levels(sepsis$Beta_bloqueador) <- c("no","si")
levels(sepsis$Otros_antihta) <- c("no","si")

#levels(sepsis$DM_2) <- c("no","si")
sepsis$DM2<- recode(sepsis$DM_2,"0='2'; 1='1'")
levels(sepsis$DM2) <- c("si", "no")

levels(sepsis$Metformina) <- c("no","si")
levels(sepsis$iSGLT2) <- c("no","si")
levels(sepsis$DDPIV) <- c("no","si")
levels(sepsis$GLP1a) <- c("no","si")
levels(sepsis$Insulina_basal) <- c("no","si")
levels(sepsis$Insulina_preprandial) <- c("no","si")
levels(sepsis$Otros_antidiabeticos) <- c("no","si")


ins_2<- sepsis[sepsis$Insulina_basal != 0, ]  ### ESTABLECE SUBSET DONDE NOREPI ES DIFERENTE A 0 
summary(ins_2$Dosis_preprandial)


library(car) 
#levels(sepsis$Hipotiroidismo) <- c("no","si")
sepsis$hipotiroidismo2<- recode(sepsis$Hipotiroidismo,"0='2'; 1='1'")
levels(sepsis$hipotiroidismo2) <- c("si", "no")


#levels(sepsis$ERC) <- c("no","si")
sepsis$ERC2<- recode(sepsis$ERC,"0='2'; 1='1'")
levels(sepsis$ERC2) <- c("si", "no")


#levels(sepsis$Tabaco) <- c("no","si")
sepsis$Tabaco2<- recode(sepsis$Tabaco,"0='2'; 1='1'")
levels(sepsis$Tabaco2) <- c("si", "no")

##levels(sepsis$Enf_coronaria) <- c("no","si")
sepsis$co<- recode(sepsis$Enf_coronaria,"0='2'; 1='1'")
levels(sepsis$co) <- c("si", "no")

##levels(sepsis$Obesidad) <- c("no","si")
sepsis$obesidad2<- recode(sepsis$Obesidad,"0='2'; 1='1'")
levels(sepsis$obesidad2) <- c("si", "no")


#levels(sepsis$Dislipidemia) <- c("no","si")
sepsis$dislipidemia2<- recode(sepsis$Dislipidemia,"0='2'; 1='1'")
levels(sepsis$dislipidemia2) <- c("si", "no")



#levels(sepsis$ACV) <- c("no","si")
sepsis$ACV2<- recode(sepsis$ACV,"0='2'; 1='1'")
levels(sepsis$ACV2) <- c("si", "no")



#levels(sepsis$Fib_aur) <- c("no","si")
sepsis$FA<- recode(sepsis$Fib_aur,"0='2'; 1='1'")
levels(sepsis$FA) <- c("si", "no")


levels(sepsis$Autoinmune) <- c("no","si")
sepsis$Auto2<- recode(sepsis$Autoinmune,"0='2'; 1='1'")
levels(sepsis$Auto2) <- c("si", "no")





levels(sepsis$Sepsis) <- c("Colangitis","Diverticulitis","Endocarditis","Osteomielitis","Peritonitis","Empiema","Epoc_sobreinf","NAC","Pie_diabetico","ISO_cx_plástica","Urinaria")
levels(sepsis$Alt_C) <- c("no","si")
levels(sepsis$Norepi) <- c("no","si")
levels(sepsis$Vasopresina) <- c("no","si")
levels(sepsis$ATB_1) <- c("Ampicilina sulbactam","Cefalexina","Cefepime","Oxacilina","Meropenem","Ceftazidima avibactam","Penicilina benzatínica","Piperacilina tazobactam","Vancomicina","Linezolid","Tigeciclina","Anfotericina_B","Caspofungina","Claritromicina","TMP_SMX","Tetraconjugado","Ciprofloxacino","Ninguno")
levels(sepsis$ATB_2) <- c("Ampicilina sulbactam","Cefalexina","Cefepime","Oxacilina","Meropenem","Ceftazidima avibactam","Penicilina benzatínica","Piperacilina tazobactam","Vancomicina","Linezolid","Tigeciclina","Anfotericina_B","Caspofungina","Claritromicina","TMP_SMX","Tetraconjugado","Ciprofloxacino","Ninguno")
levels(sepsis$ATB_3) <- c("Ampicilina sulbactam","Cefalexina","Cefepime","Oxacilina","Meropenem","Ceftazidima avibactam","Penicilina benzatínica","Piperacilina tazobactam","Vancomicina","Linezolid","Tigeciclina","Anfotericina_B","Caspofungina","Claritromicina","TMP_SMX","Tetraconjugado","Ciprofloxacino","Ninguno")
levels(sepsis$Cultivos) <- c("E. coli","K. pneumoniae","P. aeruginosa","SAMR","SAMS","S. marcecens","Candida","TBC","Sars-cov-2","No Id")
levels(sepsis$IOT) <- c("no","si")
levels(sepsis$IRA) <- c("no","si")
levels(sepsis$Dialisis) <- c("no","si")
##levels(sepsis$Muerte) <- c("vivo","muerto")
library(car) 
sepsis$Mort<- recode(sepsis$Muerte,"0='2'; 1='1'")
levels(sepsis$Mort) <- c("si", "no")


# TABLAS

tabla1<-table(sepsis$Sexo)
tabla1
tabla2<-table(sepsis$Hospital) 
tabla2
tabla3<-table(sepsis$Proced) 
tabla3
tabla4<-table(sepsis$Reg_salud)
tabla4 
tabla5<-table(sepsis$HTA) 
tabla5
tabla6<-table(sepsis$ARA_2) 
tabla6
tabla7<-table(sepsis$IECA) 
tabla7
tabla8<-table(sepsis$Tiazidas) 
tabla8
tabla9<-table(sepsis$diur_asa) 
tabla9
tabla10<-table(sepsis$Calcio.antagonista) 
tabla10
tabla11<-table(sepsis$Beta_bloqueador) 
tabla11
tabla12<-table(sepsis$Otros_antihta) 
tabla12
tabla13<-table(sepsis$DM_2) 
tabla13
tabla14<-table(sepsis$Metformina) 
tabla14
tabla15<-table(sepsis$iSGLT2) 
tabla15
tabla16<-table(sepsis$DDPIV) 
tabla16
tabla17<-table(sepsis$GLP1a) 
tabla17
tabla18<-table(sepsis$Insulina_basal)
tabla18
tabla19<-table(sepsis$Insulina_preprandial) 
tabla19
tabla20<-table(sepsis$Otros_antidiabeticos) 
tabla20
tabla21<-table(sepsis$Hipotiroidismo) 
tabla21
tabla22<-table(sepsis$ERC) 
tabla22
tabla23<-table(sepsis$Tabaco) 
tabla23
tabla24<-table(sepsis$Enf_coronaria) 
tabla24
tabla25<-table(sepsis$Obesidad) 
tabla25
tabla26<-table(sepsis$Dislipidemia) 
tabla26
tabla27<-table(sepsis$ACV) 
tabla27
tabla28<-table(sepsis$Fib_aur) 
tabla28
tabla29<-table(sepsis$Autoinmune) 
tabla29
tabla30<-table(sepsis$Sepsis) 
tabla30
tabla31<-table(sepsis$Alt_C) 
tabla31
tabla32<-table(sepsis$Norepi) 
tabla32
tabla33<-table(sepsis$Vasopresina) 
tabla33
tabla34<-table(sepsis$ATB_1) 
tabla34
tabla35<-table(sepsis$ATB_2) 
tabla35
tabla36<-table(sepsis$ATB_3) 
tabla36
tabla37<-table(sepsis$Cultivos)
tabla37
tabla38<-table(sepsis$IOT) 
tabla38
tabla39<-table(sepsis$IRA) 
tabla39
tabla40<-table(sepsis$Dialisis) 
tabla40
tabla41<-table(sepsis$Mort) 
tabla41


# FRECUENCIAS RELATIVAS (con %)

proporciones1<-prop.table(tabla1)   
proporciones1*100
proporciones2<-prop.table(tabla2)   
proporciones2*100
proporciones3<-prop.table(tabla3)   
proporciones3*100
proporciones4<-prop.table(tabla4)   
proporciones4*100
proporciones5<-prop.table(tabla5)   
proporciones5*100
proporciones6<-prop.table(tabla6)   
proporciones6*100
proporciones7<-prop.table(tabla7)   
proporciones7*100
proporciones8<-prop.table(tabla8)   
proporciones8*100
proporciones9<-prop.table(tabla9)   
proporciones9*100
proporciones10<-prop.table(tabla10)   
proporciones10*100
proporciones11<-prop.table(tabla11)   
proporciones11*100
proporciones12<-prop.table(tabla12)   
proporciones12*100
proporciones13<-prop.table(tabla13)   
proporciones13*100
proporciones14<-prop.table(tabla14)   
proporciones14*100
proporciones15<-prop.table(tabla15)   
proporciones15*100
proporciones16<-prop.table(tabla16)   
proporciones16*100
proporciones17<-prop.table(tabla17)   
proporciones17*100
proporciones18<-prop.table(tabla18)   
proporciones18*100
proporciones19<-prop.table(tabla19)   
proporciones19*100
proporciones20<-prop.table(tabla20)   
proporciones20*100
proporciones21<-prop.table(tabla21)   
proporciones21*100
proporciones22<-prop.table(tabla22)   
proporciones22*100
proporciones23<-prop.table(tabla23)   
proporciones23*100
proporciones24<-prop.table(tabla24)   
proporciones24*100
proporciones25<-prop.table(tabla25)   
proporciones25*100
proporciones26<-prop.table(tabla26)   
proporciones26*100
proporciones27<-prop.table(tabla27)   
proporciones27*100
proporciones28<-prop.table(tabla28)   
proporciones28*100
proporciones29<-prop.table(tabla29)   
proporciones29*100
proporciones30<-prop.table(tabla30)   
proporciones30*100
proporciones31<-prop.table(tabla31)   
proporciones31*100
proporciones32<-prop.table(tabla32)   
proporciones32*100
proporciones33<-prop.table(tabla33)   
proporciones33*100
proporciones34<-prop.table(tabla34)   
proporciones34*100
proporciones35<-prop.table(tabla35)   
proporciones35*100
proporciones36<-prop.table(tabla36)   
proporciones36*100
proporciones37<-prop.table(tabla37)   
proporciones37*100
proporciones38<-prop.table(tabla38)   
proporciones38*100
proporciones39<-prop.table(tabla39)   
proporciones39*100
proporciones40<-prop.table(tabla40)   
proporciones40*100
proporciones41<-prop.table(tabla41)   
proporciones41*100

### GRAFICAS DESCRIPTIVAS 

## HISTOGRAMA

dev.new() 
hist(sepsis$Edad,col="lightblue", main="Histograma edad de los pacientes",xlab="Edad (años)", ylab = "Frecuencia (%)", freq = T, xlim = c(10, 110), ylim = c(0, 60))
abline(v = mean(sepsis$Edad), col="red", lwd=3, lty=2)
abline(v = median(sepsis$Edad), col="blue", lwd=3, lty=2)
legend(x = "topright", legend = c("Media", "Mediana"), fill = c("red", "blue"), 
       title = "Medidas de tendencia central")



dev.new() 
hist(sepsis$Peso,col="lightblue", main="Histograma del peso",xlab="Peso (kg)", ylab = "Frecuencia (%)", freq = T, xlim = c(40, 120), ylim = c(0, 50))
abline(v = mean(sepsis$Peso), col="red", lwd=3, lty=2)
abline(v = median(sepsis$Peso), col="blue", lwd=3, lty=2)
legend(x = "topright", legend = c("Media", "Mediana"), fill = c("red", "blue"), 
       title = "Medidas de tendencia central")


dev.new() 
hist(sepsis$Talla,col="lightblue", main="Histograma de la talla",xlab="Talla (m)", ylab = "Frecuencia (%)", freq = T, xlim = c(1.5, 2), ylim = c(0, 50))
abline(v = mean(sepsis$Talla), col="red", lwd=3, lty=2)
abline(v = median(sepsis$Talla), col="blue", lwd=3, lty=2)
legend(x = "topright", legend = c("Media", "Mediana"), fill = c("red", "blue"), 
       title = "Medidas de tendencia central")




dev.new() 
hist(sepsis$IMC,col="lightblue", main="Histograma del IMC",xlab="IMC (kg/m2)", ylab = "Frecuencia (%)", freq = T, xlim = c(15, 40), ylim = c(0, 50))
abline(v = mean(sepsis$IMC), col="red", lwd=3, lty=2)
abline(v = median(sepsis$IMC), col="blue", lwd=3, lty=2)
legend(x = "topright", legend = c("Media", "Mediana"), fill = c("red", "blue"), 
       title = "Medidas de tendencia central")




## PIE CHARTS

# SEXO

dev.new()
p1=proporciones1*100
x1 = tabla1
y1=c("Hombres","Mujeres")
z1=paste(y1,p1,"%")
pie(x1, labels=z1, col=c("lightblue","lightgreen"), radius= 0.9, edges=200, main="Sexo de los pacientes")


# HOSPITALES

dev.new()
p2=proporciones2*100
x2 = tabla2
y2=levels(sepsis$Hospital)
z2=paste(y2,p2,"%")
pie(x2, labels=z2, col=rainbow(length(y2)), radius= 0.9, edges=200, main="Hospital tratante")



# CIUDADES DE PROCEDENCIA

dev.new()
p3=proporciones3*100
x3 = tabla3
y3=levels(sepsis$Proced)
z3=paste(y3,p3,"%")
pie(x3, labels=z3, col=rainbow(length(y3)), radius= 0.7, edges=100, main="Ciudad de origen")

# REGIMEN DE SALUD

dev.new()
p4=proporciones4*100
x4 = tabla4
y4=levels(sepsis$Reg_salud)
z4=paste(y4,p4,"%")
pie(x4, labels=z4, col=rainbow(length(y4)), radius= 0.9, edges=200, main="Regimen de salud")


# ANTECEDENTES PATOLOGICOS

dev.new()
p5=proporciones5*100
p13=proporciones13*100
p21=proporciones21*100
p22=proporciones22*100
p23=proporciones23*100
p24=proporciones24*100
p25=proporciones25*100
p26=proporciones26*100
p27=proporciones27*100 
p28=proporciones28*100
p29=proporciones29*100
barplot(horiz=FALSE, space=c(0,0.2), las=c(0), cex.main=2, height= cbind(HTA=p5, Dislipidemia=p26, Hipotiroidismo=p21, Tabaquismo=p23, DM2=p13, 
Fib_auricular=p28, ACV=p27, Autoinmunidad=p29, ERC=p22, Enf_Coronaria=p24, Obesidad=p25), beside = TRUE, width=c(3.2), col=c(2,1), 
legend.text=c("Sano","Enfermo"),  main="Prevalencia de antecedentes patologicos", ylim=c(0,100), xlim=c(0,100), ylab="%", xlab="Enfermedad")

# TRATAMIENTO ANTI HTA

dev.new()
p6=proporciones6*100
p7=proporciones7*100
p8=proporciones8*100
p9=proporciones9*100
p10=proporciones10*100
p11=proporciones11*100
p12=proporciones12*100
barplot(horiz=FALSE, space=c(0,0.2), las=c(0), cex.main=2, height= cbind(ARA_2=p6,
IECA=p7, Tiazidas=p8, diur_asa=p9, Ca_antagonis=p10, Beta_bloq=p11, Otros=p12), beside = TRUE, width=c(3.2), col=c(2,1), 
legend.text=c("No utiliza","Si utiliza"),  main="Anti Hipertensivos", ylim=c(0,100), xlim=c(0,65), ylab="%", xlab="Medicamentos")



# TRATAMIENTO NORMOGLUCEMIANTE

dev.new()
p14=proporciones14*100
p15=proporciones15*100
p16=proporciones16*100
p17=proporciones17*100
p18=proporciones18*100
p19=proporciones19*100
p20=proporciones20*100
barplot(horiz=FALSE, space=c(0,0.2), las=c(0), cex.main=2, height= cbind
(Metformina=p14, i_SGLT2=p15, DDP_IVi=p16, GLP1a=p17, Ins_basal=p18, Ins_prepran=p19, Otros=p20), beside = TRUE, width=c(3.2), col=c(2,1), legend.text=c("No utiliza","Si utiliza"),  main="Normoglucemiantes", ylim=c(0,100), xlim=c(0,65), ylab="%", xlab="Medicamentos")

# MOTIVO DE INFECCIÓN


dev.new()
p30=proporciones30*100
x30 = tabla30
y30=levels(sepsis$Sepsis)
z30=paste(y30,p30,"%")
pie(x30, labels=z30, col=rainbow(length(y30)), radius= 0.8, edges=200, main="Etiología de la sepsis")

# ALTERACIÓN DE LA CONSCIENCIA

dev.new()
p31=proporciones31*100
x31 = tabla31
y31=levels(sepsis$Alt_C)
z31=paste(y31,p31,"%")
pie(x31, labels=z31, col=rainbow(length(y30)), radius= 1, edges=200, main="Alteración de la consciencia")


# Alteración de la consciencia vs mortalidad

dev.new()
par(mfrow=c(1,2))
p31=proporciones31*100
x31 = tabla31
y31=levels(sepsis$Alt_C)
z31=paste(y31,p31,"%")
pie(x31, labels=z31, col=c("lightblue","lightgreen"), radius= 2, edges=200, main="Alteración de la consciencia")
plot(sepsis$Alt_C, sepsis$Muerte, main="Alteración de la consciencia vs mortalidad", 
xlab="Alteración de la consciencia", ylab="% mortalidad", col=c("lightblue","lightgreen"))


# Norepinefrina - Vasopresina

dev.new()
par(mfrow=c(2,2))
p32=proporciones32*100
x32 = tabla32
y32=levels(sepsis$Norepi)
z32=paste(y32,p32,"%")
pie(x32, labels=z32, col=c("lightblue","lightgreen"), radius= 1, edges=200, main="Norepinefrina")
plot(sepsis$Norepi, sepsis$Muerte, main="Requerimiento de Norepinefrina vs mortalidad", 
xlab="Uso de norepinefrina", ylab="% mortalidad", col=c("lightblue","lightgreen"))
p33=proporciones33*100
x33 = tabla33
y33=levels(sepsis$Vasopresina)
z33=paste(y32,p32,"%")
pie(x33, labels=z33, col=c("lightblue","lightgreen"), radius= 1, edges=200, main="Vasopresina")
plot(sepsis$Vasopresina, sepsis$Muerte, main="Requerimiento de Vasopresina vs mortalidad", 
xlab="Uso de vasopresina", ylab="% mortalidad", col=c("lightblue","lightgreen"))


# Mortalidad vs Aislamiento


dev.new()
p37=proporciones37*100
x37 = tabla37
y37=levels(sepsis$Cultivos)
z37=paste(y37,p37,"%")
pie(x37, labels=z37, col=rainbow(length(y37)), radius= 1, edges=200, main="Microorganismos")

dev.new()
plot(sepsis$Cultivos, sepsis$Muerte, main="Mortalidad vs Aislamiento", 
xlab="Microorganismo", ylab="% mortalidad", col=c("lightblue","lightgreen"))


# Requerimiento de intubación orotraqueal vs mortalidad

dev.new()
par(mfrow=c(1,2))
p38=proporciones38*100
x38 = tabla38
y38=levels(sepsis$IOT)
z38=paste(y38,p38,"%")
pie(x38, labels=z38, col=c("lightblue","lightgreen"), radius= 2, edges=200, main="Requerimiento de IOT")
plot(sepsis$IOT, sepsis$Muerte, main="Requerimiento de IOT vs mortalidad", 
xlab="IOT", ylab="% mortalidad", col=c("lightblue","lightgreen"))

# Injuria renal aguda y dialisis vs mortalidad

dev.new()
par(mfrow=c(2,2))

p39=proporciones39*100
x39 = tabla39
y39=levels(sepsis$IRA)
z39=paste(y39,p39,"%")
pie(x39, labels=z39, col=c("lightblue","lightgreen"), radius= 1, edges=200, main="Injuria renal aguda")
plot(sepsis$IRA, sepsis$Muerte, main="Injuria renal aguda vs mortalidad", 
     xlab="Injuria renal aguda", ylab="% mortalidad", col=c("lightblue","lightgreen"))

p40=proporciones40*100
x40 = tabla40
y40=levels(sepsis$Dialisis)
z40=paste(y40,p40,"%")
pie(x40, labels=z40, col=c("lightblue","lightgreen"), radius= 1, edges=200, main="Requerimiento de dialisis")
plot(sepsis$Dialisis, sepsis$Muerte, main="Requerimiento de Dialisis vs mortalidad", 
     xlab="Dialisis", ylab="% mortalidad", col=c("lightblue","lightgreen"))


# CAJAS Y BIGOTES

# IMC VS MORTALIDAD

dev.new() 
boxplot(sepsis$IMC,col="green", main="IMC vs mortalidad",xlab="kg/m2",ylab="Muerte")
sepsis$Muerte
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(IMC ~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="IMC vs mortalidad", ylab="Kg/m2", xlab="Mortalidad")


dev.new()
par(mfrow=c(2,2))
sepsis$Muerte
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(Tam_inicial~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="TAM_ingreso vs mortalidad", ylab="mmHg", xlab="Mortalidad")
boxplot(Tam_12h~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="TAM 12h vs mortalidad", ylab="mmHg", xlab="Mortalidad")
boxplot(Tam_24h~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="TAM 24h vs mortalidad", ylab="mmHg", xlab="Mortalidad")
ay <- ((sepsis$Tam_24h - sepsis$Tam_inicial)/sepsis$Tam_inicial)*100
boxplot(ay~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta TAM vs mortalidad", ylab="% cambio", xlab="Mortalidad")

## DELTA LACTATO, LLENADO CAPILAR, PH, HCO3, N/L Y PCR  vs Mortalidad

dev.new()
par(mfrow=c(1,3))

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(sepsis$Lactato_inicial~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Lactato inicial vs Mortalidad", ylab="mmol/l", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(sepsis$Lactato_24h~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Lactato 24 h vs Mortalidad", ylab="mmol/l", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(((sepsis$Lactato_24h - sepsis$Lactato_inicial)/sepsis$Lactato_inicial*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta de Lactato vs Mortalidad", ylab="%", xlab="Mortalidad")

dev.new()
par(mfrow=c(1,3))
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(sepsis$capilar~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Llenado capilar inicial vs Mortalidad", ylab="segundos", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(sepsis$capilar24~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Llenado capilar 24 h vs Mortalidad", ylab="segundos", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(((sepsis$capilar24 - sepsis$capilar)/sepsis$capilar*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta de llenado capilar vs Mortalidad", ylab="%", xlab="Mortalidad")




muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(((sepsis$pH24 - sepsis$ph)/sepsis$ph*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta de pH vs Mortalidad", ylab="%", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(((sepsis$Hco3_24 - sepsis$Hco3)/sepsis$Hco3*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta HCO3 vs Mortalidad", ylab="%", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(((sepsis$NL_24h - sepsis$NL)/sepsis$NL*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta de ratio Neutrofilos/Linfocitos vs Mortalidad", ylab="%", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(((sepsis$PCR_24h - sepsis$PCR_inicial)/sepsis$PCR_inicial*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta de PCR vs Mortalidad", ylab="%", xlab="Mortalidad")

## GLUCOSILADA Y CV_GLUCEMICO VS MORTALIDAD


dev.new()
par(mfrow=c(1,2))
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot((sepsis$Glucosilada)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Glucosilada vs Mortalidad", ylab="%", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot((sepsis$CV_gluc)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Variabilidad glucemica vs Mortalidad", ylab="%", xlab="Mortalidad")


## DOSIS DE NOREPINEFRINA VS MORTALIDAD


dev.new()
par(mfrow=c(1,3))
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot((sepsis$Norepi_0)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Dosis de NE_inicial vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot((sepsis$Norepi_24)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Dosis de NE_24h vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad")

muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(((sepsis$Norepi_24 - sepsis$Norepi_0)/sepsis$Norepi_0*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta dosis de NE vs Mortalidad", ylab="%", xlab="Mortalidad")





## SHOCK INDEX Y DIASTOLIC INDEX VS MORTALIDAD


dev.new()
par(mfrow=c(2,2))
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot((sepsis$s_index0)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Shock_index_0h vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")
boxplot((sepsis$s_index12)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Shock_index_12h vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")
boxplot((sepsis$s_index24)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Shock_index_24h vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")
boxplot(((sepsis$s_index24 - sepsis$s_index0)/sepsis$s_index0*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta Shock_index vs Mortalidad", ylab="%", xlab="Mortalidad")


dev.new()
par(mfrow=c(2,2))
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot((sepsis$fctad_inicial)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Diastolic_index_0h vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")
boxplot((sepsis$fctad_12h)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Diastolic_index_12h vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")
boxplot((sepsis$fctad_24h)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Diastolic_index_24h vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")
boxplot(((sepsis$fctad_24h - sepsis$fctad_inicial)/sepsis$fctad_inicial*100)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Delta Diastolic_index vs Mortalidad", ylab="%", xlab="Mortalidad")





### ANALISIS ANTERIOR CON UN SUBSET DE DOSIS INICIAL DE NE != 0 (DIFERENTE A 0 MCG/KG/MIN)

fff<- sepsis[sepsis$Norepi_0 != 0, ]  ### ESTABLECE SUBSET DONDE NOREPI ES DIFERENTE A 0 
muerte3<-factor(fff$Muerte)
levels(muerte3)<- c("vivo","muerto")
dev.new()
par(mfrow=c(1,3))
boxplot((fff$Norepi_0)~ muerte3, data = fff,col=c("lightgreen","lightblue"),labels=levels(muerte3), main="Dosis de NE_inicial vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad", ylim=c(0,0.5))
boxplot((fff$Norepi_24)~ muerte3, data = fff,col=c("lightgreen","lightblue"),labels=levels(muerte3), main="Dosis de NE_24 h vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad", ylim=c(0,0.6))
boxplot(((fff$Norepi_24 - fff$Norepi_0)/fff$Norepi_0*100)~ muerte3, data = fff,col=c("lightgreen","lightblue"),labels=levels(muerte3), main="Delta de NE vs Mortalidad", ylab="%", xlab="Mortalidad", ylim=c(-100,200))


# FRECUENCIA DE MORTALIDAD SEGÚN CIUDAD (SUBSET DE MORTALIDAD = 1)

rrr<- sepsis[sepsis$Muerte == 1, ]  ### ESTABLECE SUBSET DONDE MUERTE ES POSITIVO (1)
procedencia<-factor(rrr$Proced)
levels(procedencia)<-c("Bello","Caldas","Cali","Envigado","Medellin","Pasto","Popayan","Quibdo","S_Quilichao","Tumaco","Urrao","Yarumal")
tx <- table(rrr$Muerte, procedencia)
dev.new()
barplot(tx, main="Mortalidad por región", horiz=1, las=1, xlim=c(0,25), col=c("lightgreen"))


## DIAGRAMAS DE DISPERSIÓN

fff ## SUBSET DE NE > 0

require(stats)
fff<- sepsis[sepsis$Norepi_0 != 0, ]
delta_NE <- ((fff$Norepi_24 - fff$Norepi_0)/fff$Norepi_0*100) 
dev.new()
reg<-lm(fff$CV_gluc ~ delta_NE)
plot(fff$CV_gluc, delta_NE, main="Delta de NE vs Coeficiente de variabilidad glucemico", ylab="Delta NE (%)", xlab= "C_variab gluc %") 
abline(reg, col="red") 

view(fff)

delta_NE




fff<- sepsis[sepsis$Muerte == 1, ]
delta_NE <- ((fff$Norepi_24 - fff$Norepi_0)/fff$Norepi_0*100) 
dev.new()
reg<-lm(fff$CV_gluc ~ delta_NE)
plot(fff$CV_gluc, delta_NE, main="Delta de NE vs Coeficiente de variabilidad glucemico", ylab="Delta NE (%)", xlab= "C_variab gluc %") 
abline(reg, col="red") 


fff<- sepsis[sepsis$Norepi_0 != 0, ]
dev.new()
reg<-lm(fff$Lactato_inicial ~ fff$Norepi_0)
plot(fff$CV_gluc, fff$Norepi_0, main="Delta de NE vs Coeficiente de variabilidad glucemico", ylab="Delta NE (%)", xlab= "C_variab gluc %") 
abline(reg, col="red") 

daro<- ((sepsis$Lactato_24h - sepsis$Lactato_inicial)/sepsis$Lactato_inicial)
dev.new()
plot(fff$CV_gluc, fff$fctad_inicial, main="Coeficiente de variabilidad glucemico vs Indice diastolico", ylab="Diast_Index (lpm/mmHg)", xlab= "CV_gluc (%)")
  
## ESTADISTICA DESCRIPTIVA 

mean(sepsis$Edad)
mean(sepsis$Peso)
mean(sepsis$Talla)
mean(sepsis$IMC)
mean(sepsis$Fc_inicial)
mean(sepsis$Fc_12h)
mean(sepsis$Fc_24h)
mean(sepsis$Tam_inicial)
mean(sepsis$Tam_12h)
mean(sepsis$Tam_24h)
mean(sepsis$s_index0)
mean(sepsis$s_index12)
mean(sepsis$s_index24)
mean(sepsis$fctad_inicial)
mean(sepsis$fctad_12h)
mean(sepsis$fctad_24h)
mean(sepsis$CV_gluc)
mean(sepsis$Norepi_0)
mean(sepsis$Norepi_24)
mean(sepsis$Dias_iot)




sd()  ## Desviación estandar
var()   ## varianza
cv<- function(x){sd(x)/mean(x)*100}  ### FUNCIONES EN R (EJ: COEFICIENTE DE VARIABILIDAD)
cv(sepsis$Edad)
cv(sepsis$Peso)
cv(sepsis$Talla)
cv(sepsis$CV_gluc)  ## COEFIECIENTE DE VARIABILIDAD DE LOS COEFICIENTES DE VARIABILIDAD GLUCEMICOS.

##### INFERENCIAL
##### INFERENCIAL
##### INFERENCIAL
##### INFERENCIAL

library("funModeling")
summary(sepsis$CV_gluc)
describe(sepsis$CV_gluc)
profiling_num (sepsis$CV_gluc)

dev.new() 
hist(sepsis$CV_gluc,col="lightblue", main ="histograma CV_glucemica" ,xlab="%", freq = F, xlim = c(10,45))
lines(density(sepsis$CV_gluc))
abline(v = MeanCI(sepsis$CV_gluc,conf.level = 0.99), col="green", lwd=3, lty=2)
abline(v = MeanCI(sepsis$CV_gluc,conf.level = 0.95), col="orange", lwd=3, lty=2)
abline(v = MeanCI(sepsis$CV_gluc,conf.level = 0.90), col="red", lwd=3, lty=2)
abline(v = mean(sepsis$CV_gluc), col="black", lwd=3, lty=2)
legend(x = "topright", legend = c("IC 99%_media","IC 95%_media","IC 90%_media","Media"), fill = c("green","orange","red","black"))


dev.new() 
hist(sepsis$Glucosilada,col="deeppink", main ="histograma CV_glucemica" ,xlab="%", freq = F)
lines(density(sepsis$Glucosilada))

#Ejercicios 2: Intervalo de Confianza 95% para la media 
#Opcin 1
library(Publish)
ci.mean(sepsis$CV_gluc, 0.05)
ci.mean(sepsis$CV_gluc, 0.01)
ci.mean(sepsis$CV_gluc, 0.1)
#Opcin 2
library(DescTools)
MeanCI(sepsis$CV_gluc,conf.level=0.95)
MeanCI(sepsis$CV_gluc,conf.level=0.90)
MeanCI(sepsis$CV_gluc,conf.level=0.99)


#Ejercicios 3: Intervalos de Confianza 90% y 99% para la media 
ci.mean(sepsis$CV_gluc,0.01)
ci.mean(presion$C,0.1)

#Ejercicios 4: Prueba de hip?tesis para un valor de la media (media de pas= 140Hgmm) 
t.test(sepsis$CV_gluc,mu=32)

t.test(sepsis$CV_gluc,mu=19)

qt(0.95,199)



#Ejercicios 5:crear una variable "pas_alta" para identificar individuos con pas??? 160 mmHg
library(car) 
sepsis$meta<-recode(sepsis$CV_gluc,"0:30='2'; 30.01:50='1'")
sepsis$meta <- as.factor(sepsis$meta)
# Etiquetar la nueva variable
levels(sepsis$meta) <- c("si", "no")
# Tabla de frecuencias para la nueva variable
ttr<-table(ggo)
ttr
pttr<-prop.table(ttr)   
pttr*100
pttr<-paste(pttr*100,"%")
pttr


#Ejercicios 6: Intervalo de Confianza para la proporci?n (pas ??? 160 mmHg)
#Opci?n 1 
library(PropCIs)
exactci(421, 500,
        conf.level=0.95)

exac

#Opci?n 2: IC exacto binomial 
library (DescTools)
BinomCI(41, 200,
        conf.level = 0.95,
        method = "clopper-pearson")

#Ejercicios 7: Prueba de hip?tesis para una proporci?n (pas ??? 160 mmHg))
#Opcion1: aproximaci?n normal

prop.test(29,200,0.205)
#Opcion2: Test exacto binomial 
binom.test(127,318,0.25)

qchisq(0.05, 1, lower.tail = F)

table(presion$enf_cardiaca)

x<-table(ggo, sepsis$Mort)
t(x)
prop.test(x, correct= FALSE)
library(DescTools)
OddsRatio(x,conf.level=0.95)


binom.test(51,235,(1/6),alternative="two.sided")









#a) tabla de contingencia



#b) Proporciones
margin.table (R4, 1) ## Frecuencias marginales por filas 
margin.table (R4, 2) ## Frecuencias marginales por columnas

prop.table(R4)       ## Proporciones totales  
prop.table(R4, 1)    ## Proporciones por columnas
prop.table(R4, 2)    ## Proporciones por filas
round(100*prop.table(R4, 1), dig=2 )    ## Porcentajes por filas

round(100*prop.table(R4), dig=2 )    ## Porcentajes total 2 x 2 

#Gr?fico de sectores para describir una tabla
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R4[1,], col=col.1, main="CV_Glucemico > 25%", lab=lab.bajo )
pie(R4[2,], col=col.1, main="CV_Glucemico ≤ 25%", lab=lab.bajo )

#c) Prueba ji-cuadrado: comparar proporciones
chisq.test(R4)
chisq.test(R4)$p.value
chisq.test(R4)$expected
#Valor te?rico de ji-cuadrado con 1 grado de libertad y alfa=0,05 
qchisq(0.05, 1, lower.tail = F) 

#d)ODDS RATIO E IC !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

R1 <- table(sepsis$Sexo, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R1[1,], col=col.1, main="Hombre", lab=lab.bajo )
pie(R1[2,], col=col.1, main="Mujer", lab=lab.bajo )
oddsratio(R1)

R2 <- table(sepsis$Hospital, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R2[1,], col=col.1, main="Farallones", lab=lab.bajo )
pie(R2[2,], col=col.1, main="León XIII", lab=lab.bajo )
oddsratio(R2)

R3 <- table(sepsis$Reg_salud, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R3[1,], col=col.1, main="Subsidiado", lab=lab.bajo )
pie(R3[2,], col=col.1, main="Contributivo", lab=lab.bajo )
oddsratio(R3)

## CV_GLUCEMICO

library(epitools) 
oddsratio(R4)





sepsis$meta3<-recode(sepsis$CV_gluc,"0:20='2'; 20.01:50='1'")
sepsis$meta3 <- as.factor(sepsis$meta3)
levels(sepsis$meta3) <- c("si", "no")
tmet3<-table(sepsis$meta3, sepsis$Mort)
oddsratio(tmet3)

sepsis$meta2<-recode(sepsis$CV_gluc,"0:30='2'; 30.01:50='1'")
sepsis$meta2 <- as.factor(sepsis$meta2)
levels(sepsis$meta2) <- c("si", "no")
tmet2<-table(sepsis$meta2, sepsis$Mort)
oddsratio(tmet2)


dev.new()
par(mfrow=c(2,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightblue", "lightgreen")
pie(tmet3[1,], col=col.1, main="CV_glu > 20%", lab=lab.bajo )
pie(tmet3[2,], col=col.1, main="CV_gluc < 20%", lab=lab.bajo )
pie(tmet2[1,], col=col.1, main="CV_glu > 30%", lab=lab.bajo )
pie(tmet2[2,], col=col.1, main="CV_gluc < 30%", lab=lab.bajo )



R5 <- table(sepsis$HTA2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R5[1,], col=col.1, main="HTA", lab=lab.bajo )
pie(R5[2,], col=col.1, main="No HTA", lab=lab.bajo )
oddsratio(R5)



R6 <- table(sepsis$DM2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R6[1,], col=col.1, main="DM2", lab=lab.bajo )
pie(R6[2,], col=col.1, main="No_DM2", lab=lab.bajo )
oddsratio(R6)

R7 <- table(sepsis$co, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R7[1,], col=col.1, main="Enf_Coronaria", lab=lab.bajo )
pie(R7[2,], col=col.1, main="Sin Enf_coronaria", lab=lab.bajo )
oddsratio(R7)


R8 <- table(sepsis$obesidad2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R8[1,], col=col.1, main="Obeso", lab=lab.bajo )
pie(R8[2,], col=col.1, main="No obeso", lab=lab.bajo )
oddsratio(R8)



#levels(sepsis$Hipotiroidismo) <- c("no","si")
sepsis$hipotiroidismo2<- recode(sepsis$hipotiroidismo,"0='2'; 1='1'")
levels(sepsis$hipotiroidismo2) <- c("si", "no")
R9 <- table(sepsis$hipotiroidismo2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R9[1,], col=col.1, main="Hipotiroideo", lab=lab.bajo )
pie(R9[2,], col=col.1, main="No Hipotiroideo", lab=lab.bajo )
oddsratio(R9)


#levels(sepsis$ERC) <- c("no","si")
sepsis$ERC2<- recode(sepsis$ERC,"0='2'; 1='1'")
levels(sepsis$ERC2) <- c("si", "no")
R10 <- table(sepsis$ERC2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R10[1,], col=col.1, main="ERC", lab=lab.bajo )
pie(R10[2,], col=col.1, main="No ERC", lab=lab.bajo )
oddsratio(R10)




#levels(sepsis$Tabaco) <- c("no","si")
sepsis$Tabaco2<- recode(sepsis$Tabaco,"0='2'; 1='1'")
levels(sepsis$Tabaco2) <- c("si", "no")
R11 <- table(sepsis$Tabaco2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R11[1,], col=col.1, main="Tabaquista", lab=lab.bajo )
pie(R11[2,], col=col.1, main="No tabaquista", lab=lab.bajo )
oddsratio(R11)


#levels(sepsis$Dislipidemia) <- c("no","si")
sepsis$dislipidemia2<- recode(sepsis$Dislipidemia,"0='2'; 1='1'")
levels(sepsis$dislipidemia2) <- c("si", "no")
R12 <- table(sepsis$dislipidemia2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R12[1,], col=col.1, main="Dislipidemia", lab=lab.bajo )
pie(R12[2,], col=col.1, main="No dislipidemia", lab=lab.bajo )
oddsratio(R12)

#levels(sepsis$ACV) <- c("no","si")
sepsis$ACV2<- recode(sepsis$ACV,"0='2'; 1='1'")
levels(sepsis$ACV2) <- c("si", "no")
R13 <- table(sepsis$ACV2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R13[1,], col=col.1, main="ACV", lab=lab.bajo )
pie(R13[2,], col=col.1, main="No ACV", lab=lab.bajo )
oddsratio(R13)



#levels(sepsis$Fib_aur) <- c("no","si")
sepsis$FA<- recode(sepsis$Fib_aur,"0='2'; 1='1'")
levels(sepsis$FA) <- c("si", "no")
R14 <- table(sepsis$FA, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R14[1,], col=col.1, main="Fibrilación auricular", lab=lab.bajo )
pie(R14[2,], col=col.1, main="No FA", lab=lab.bajo )
oddsratio(R14)

##levels(sepsis$Autoinmune) <- c("no","si")
sepsis$Auto2<- recode(sepsis$Autoinmune,"0='2'; 1='1'")
levels(sepsis$Auto2) <- c("si", "no")
R15 <- table(sepsis$Auto2, sepsis$Mort)
library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R15[1,], col=col.1, main="Autoinmunidad", lab=lab.bajo )
pie(R15[2,], col=col.1, main="No Autoinmunidad", lab=lab.bajo )
oddsratio(R15)



summary(sepsis$Wbc_inicial)


library(car) 
sepsis$leucocitosis3<-recode(sepsis$Wbc_24h,"0:11499='0'; 11500:80000='1'")
sepsis$leucocitosis3 <- as.factor(sepsis$leucocitosis3)

# Etiquetar la nueva variable
levels(sepsis$leucocitosis3) <- c("normal", "leucocitosis")
# Tabla de frecuencias para la nueva variable
u1<-table(sepsis$leucocitosis3)
u1
proporcion<-prop.table(u1)   
proporcion*100

sepsis$leucocitosis

wbc2<- sepsis[sepsis$Wbc_inicial > 11500, ]
summary(wbc2$Wbc_inicial)

summary(sepsis$Wbc_24h)


sepsis$corwbc=(sepsis$Wbc_24h)/(sepsis$Wbc_inicial)
sepsis$corwbc<-recode(sepsis$corwbc,"0:0.99999999999='2'; 1:100='1'")
sepsis$corwbc<- as.factor(sepsis$corwbc)

R88 <- table(sepsis$corwbc, sepsis$Mort)

library(epitools)
dev.new()
par(mfrow=c(1,2))
lab.bajo=c("Muertos", "Vivos")
col.1 = c("lightgreen", "lightblue")
pie(R88[1,], col=col.1, main="WBC_aumentan", lab=lab.bajo )
pie(R88[2,], col=col.1, main="WBC_disminuyen", lab=lab.bajo )
oddsratio(R88)




library(car)
#Test Bartlett (Parametrico) 
bartlett.test(sepsis$SOFA,sepsis$Mort)
var.test ( sepsis$SOFA ~  sepsis$Mort)

dev.new() 
hist(sepsis$PCR_inicial,col="red", main="histograma trigliceridos",xlab="trigliceridos", freq = F)


bartlett.test(sepsis$SOFA,sepsis$Mort)
var.test ( sepsis$SOFA ~  sepsis$Mort)


library(car)
t.test ( sepsis$NL ~  sepsis$Mort, var.equal=T)

library(car)
t.test ( sepsis$NL_24h ~  sepsis$Mort, var.equal=T)

dev.new()
par(mfrow=c(1,2))
boxplot ( sepsis$s_index0 ~  sepsis$Mort, col=c("lightgreen","lightblue"), 
          main="Relación N:L y mortalidad" )
boxplot ( sepsis$s_ ~  sepsis$Mort, col=c("lightgreen","lightblue"), 
          main="Relación N:L a las 24 hy mortalidad" )


library(car)
t.test ( sepsis$SOFA ~  sepsis$Mort, var.equal=F)

library(car)
t.test ( sepsis$PCR_24h ~  sepsis$Mort, var.equal=T)

summary(sepsis$s_index0)

library(car)
#Test Bartlett (Parametrico) 
bartlett.test(sepsis$s_index0,sepsis$Mort)
var.test ( sepsis$s_index0 ~  sepsis$Mort)


t.test (sepsis$s_index0 ~  sepsis$Mort, var.equal=F)


summary(sepsis$Tam_inicial)
summary(sepsis$Tam_12h)
summary(sepsis$Tam_24h)


bartlett.test(sepsis$Tam_inicial,sepsis$Mort)
var.test ( sepsis$Tam_inicial ~  sepsis$Mort)

bartlett.test(sepsis$Tam_12h,sepsis$Mort)
var.test ( sepsis$Tam_12h ~  sepsis$Mort)

bartlett.test(sepsis$Tam_24h,sepsis$Mort)
var.test ( sepsis$Tam_24h ~  sepsis$Mort)


t.test (sepsis$Tam_inicial ~  sepsis$Mort, var.equal=F)
t.test (sepsis$Tam_12h ~  sepsis$Mort, var.equal=F)
t.test (sepsis$Tam_24h ~  sepsis$Mort, var.equal=F)

summary(sepsis$fctad_inicial)
t.test (sepsis$fctad_inicial ~  sepsis$Mort, var.equal=F)






dev.new()
par(mfrow=c(1,5))
sepsis$Muerte
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(Tam_inicial~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="TAM_ingreso vs mortalidad", ylab="mmHg", xlab="Mortalidad")
boxplot(Tam_12h~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="TAM 12h vs mortalidad", ylab="mmHg", xlab="Mortalidad")
boxplot(Tam_24h~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="TAM 24h vs mortalidad", ylab="mmHg", xlab="Mortalidad")
boxplot((sepsis$s_index0)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Shock_index vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")
boxplot((sepsis$fctad_inicial)~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Diastolic_index vs Mortalidad", ylab="lpm / mmHg", xlab="Mortalidad")

summary(sepsis$Lactato_inicial)
sepsis$deltalactato = ((sepsis$Lactato_24h - sepsis$Lactato_inicial)/sepsis$Lactato_inicial)*100

sepsis$deltalactato

bartlett.test(sepsis$Lactato_inicial,sepsis$Mort)
var.test ( sepsis$Lactato_inicial ~  sepsis$Mort)
t.test (sepsis$Lactato_inicial ~  sepsis$Mort, var.equal=F)


library(car) 
sepsis$lactato3<-recode(sepsis$deltalactato,"- 800000000:0.9999999999='2'; 1:80000='1'")
sepsis$lactato3 <- as.factor(sepsis$lactato3)
levels(sepsis$lactato3) <- c("sube", "baja")

R90 <- table(sepsis$lactato3, sepsis$Mort)
oddsratio(R90)



summary(sepsis$capilar)
bartlett.test(sepsis$capilar,sepsis$Mort)
var.test ( sepsis$capilar ~  sepsis$Mort)
t.test (sepsis$capilar ~  sepsis$Mort, var.equal=T)



sepsis$deltacapilar= ((sepsis$capilar24 - sepsis$capilar)/sepsis$capilar)*100
sepsis$deltacapilar



library(car) 
sepsis$capilar3<-recode(sepsis$deltacapilar,"- 800000000:0.9999999999='2'; 1:80000='1'")
sepsis$capilar3 <- as.factor(sepsis$capilar3)
levels(sepsis$capilar3) <- c("sube", "baja")

R91 <- table(sepsis$capilar3, sepsis$Mort)
oddsratio(R91)


dev.new()
par(mfrow=c(2,2))
sepsis$Muerte
muerte2<-factor(sepsis$Muerte)
levels(muerte2)<- c("vivo","muerto")
boxplot(sepsis$Lactato_inicial~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Lactato_0h vs mortalidad", ylab="mmol/l", xlab="Mortalidad")
boxplot(sepsis$Lactato_24h ~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Lactato_24h vs mortalidad", ylab="mmol/l", xlab="Mortalidad")
boxplot(sepsis$capilar ~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Llenado_capilar_0h vs mortalidad", ylab="segundos", xlab="Mortalidad")
boxplot(sepsis$capilar24 ~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="Llenado_capilar_24h vs mortalidad", ylab="segundos", xlab="Mortalidad")

summary(sepsis$CV_gluc)


bartlett.test(sepsis$CV_gluc,sepsis$Mort)
var.test ( sepsis$CV_gluc ~  sepsis$Mort)
t.test (sepsis$CV_gluc~  sepsis$Mort, var.equal=T)


t.test (sepsis$SOFA~  sepsis$Mort, var.equal=T)

summary(sepsis$SOFA)

dev.new()
par(mfrow=c(2,3))
muerte2<-factor(sepsis$Muerte)
dmc<-factor(sepsis$DM2)
levels(dmc)<- c("diabetico","no diabetico")
levels(muerte2)<- c("vivo","muerto")
boxplot(sepsis$CV_gluc~ dmc, data = sepsis,col=c("lightgreen","lightblue"), labels=levels(dmc), main="CV_Glucemico vs DM_2", ylab="%", xlab="Diabetes mellitus 2")
boxplot(sepsis$CV_gluc ~ muerte2, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte2), main="CV_Glucemico vs mortalidad", ylab="%", xlab="Mortalidad")




dev.new()
par(mfrow=c(1,3))
muerte3<-factor(XaX$Muerte)
levels(muerte3)<- c("vivo","muerto")
boxplot(XaX$Norepi_0 ~ muerte3, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte3), main="Dosis_NE_0h vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad")
boxplot(XaX$Norepi_24 ~ muerte3, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte3), main="Dosis_NE_24h vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad")
boxplot(XaX$NE_delta ~ muerte3, data = sepsis, col=c("lightgreen","lightblue"),labels=levels(muerte3), main="Delta NE vs Mortalidad", ylab="%", xlab="Mortalidad")




library("funModeling")
profiling_num (sepsis$SOFA)

summary(XaX$Norepi_24)

table(sepsis$Norepi)

summary(XaX$Norepi_24)


bartlett.test(XaX$Norepi_24,XaX$Mort)
var.test ( XaX$Norepi_24 ~  XaX$Mort)
t.test (XaX$NE_delta ~  XaX$Mort, var.equal=F)

summary(XaX$Norepi_24)

XaX$NE_delta


dev.new()
par(mfrow=c(1,3))
mx<-factor(XaX$Mort)
levels(mx)<- c("muerto","vivo")
boxplot(XaX$Norepi_0 ~ mx, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(mx), main="Dosis_NE_0h vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad")
boxplot(XaX$Norepi_24 ~ mx, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(mx), main="Dosis_NE_24h vs Mortalidad", ylab="mcg/kg/min", xlab="Mortalidad")
boxplot(XaX$NE_delta ~ mx, data = sepsis, col=c("lightgreen","lightblue"),labels=levels(mx), main="Delta NE vs Mortalidad", ylab="%", xlab="Mortalidad")









library(car) 
XaX$Mort<- recode(XaX$Muerte,"0='2'; 1='1'")
levels(XaX$Mort) <- c("muerto", "vivo")

XaX$Mort



XaX$NE_delta <- ((XaX$Norepi_24 - XaX$Norepi_0)/XaX$Norepi_0*100) 


dev.new()
par(mfrow=c(1,1))
bartlett.test(XaX$NE_delta,XaX$Mort)
var.test (XaX$NE_delta ~  XaX$Mort)
t.test (XaX$NE_delta ~ XaX$Muerte, var.equal=F)
muerte5<-factor(XaX$Muerte)
levels(muerte5)<- c("vivo","muerto")
boxplot(XaX$NE_delta ~ muerte5, data = XaX, col=c("lightgreen","lightblue"),labels=levels(muerte5), main="Delta NE vs Mortalidad", ylab="%", xlab="Mortalidad")





XaX$Muerte

dev.new()
par(mfrow=c(2,3))
muerte3<-factor(XaX$Mort)
levels(muerte3)<- c("vivo","muerto")
boxplot(XaX$NE_delta ~ muerte3, data = sepsis,col=c("lightgreen","lightblue"),labels=levels(muerte3), main="Dosis_NE_0h vs Mortalidad", ylab="%", xlab="Mortalidad")



####### RELACIÒN LINEAL 



XaX<- sepsis[sepsis$Norepi_0 != 0, ]

XaX$Norepi_0




dev.new()
par(mfrow=c(1,2))
plot(XaX$CV_gluc, XaX$Norepi_0, pch=10, cex=2, col=c("deeppink"), main="CV_Glucemico vs Dosis de norepinefrina_0h",
     xlab="CV_glucemico (%)", ylab="Dosis de NE (mcg/kg/min)")
plot(XaX$CV_gluc, XaX$Norepi_24, pch=10, cex=2, col=c("deeppink"), main="CV_Glucemico vs Dosis de norepinefrina_24h",
     xlab="CV_glucemico (%)", ylab="Dosis de NE (mcg/kg/min)")


dev.new()
par(mfrow=c(1,2))
plot(XaX$Norepi_0, XaX$NL, pch=10, cex=2, col=c("deeppink"), main="CV_Glucemico vs Dosis de norepinefrina_0h",
     xlab="CV_glucemico (%)", ylab="Dosis de NE (mcg/kg/min)")
plot(XaX$Lactato_24h, XaX$capilar24, pch=10, cex=2, col=c("deeppink"), main="CV_Glucemico vs Dosis de norepinefrina_24h",
     xlab="CV_glucemico (%)", ylab="Dosis de NE (mcg/kg/min)")





cor.test(XaX$CV_gluc, XaX$Norepi_24, method = "spearman",exact=FALSE)

library(nortest)
lillie.test (sepsis$CV_gluc)


cor(XaX$CV_gluc, XaX$Norepi_0, method = "pearson")
cor(XaX$CV_gluc, XaX$Norepi_24, method = "pearson")

hist(sepsis$CV_gluc,col="red", main="histograma trigliceridos",xlab="trigliceridos", freq = F)


library("funModeling")
profiling_num (sepsis$CV_gluc)
summary(sepsis$CV_gluc)




library(corrplot)
w.cor= cor (sepsis[,3:5 97],method = "spearman",use="pairwise.complete.obs")
dev.new()
corrplot(w.cor)
dev.new()
corrplot(w.cor, order="hclust")


%%Prijimanie udajov
if exist('s2','var')
    clear s2
end
s2 = serialport('COM131', 9600);
output=read(s2,1,"char")
SetPoint=double(output)
clear s2

pause(5)

%%Nastavenie parametrov motora, regulatora a filtrov
J=0.85e-04;
B=0;
w2=1000;
Td=2/w2;
w0=(J+B*Td)/(3*J*Td)

Kp=1/30*(3*pi*J*Td*w0^2-pi*B)
Ti=(30*Kp)/(pi*J*w0^3*Td)
w1=1/Ti;
xi1=1;
xi2=1;

%%Vysielanie udajov
instrreset % uvolnenie portov
s1 = serial('COM141','BaudRate', 9600);
fopen(s1)
sim('simulacia_zadanie')
fprintf(s1,'OK\n');
fclose(s1)
clear s1


%fprintf(s1,'5')
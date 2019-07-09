# ----------------------------------------------------------------------------
# -- Simulador geologico
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronic Technology. Rey Juan Carlos University (urjc.es)
# -- July-2019
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

# to execute from the FreeCAD console:
#  execute freecad from the cmd console on the directory
# "C:\Program Files\FreeCAD 0.16\bin\freecad" base.py

# to excute from command line in windows:
# "C:\Program Files\FreeCAD 0.16\bin\freecadcmd" base.py

# with FreeCAD 0.18 Python 3
#exec(open("geo_mesa.py").read())

import os
import sys
import math
import FreeCAD
import FreeCADGui
import Part
import Draft
import logging  # to avoid using print statements
import time
#import copy
#import Mesh
import DraftVecUtils


# to get the current directory. Freecad has to be executed from the same
# directory this file is
filepath = os.getcwd()
#filepath = "./"
#filepath = "F/urjc/proyectos/2016_platform_cell/device/planos/python/"
#filepath = "C:/Users/felipe/urjc/proyectos/2016_platform_cell/device/planos/python/"


# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath) 
# Either one of these 2 to select the path, inside the tree, copied by
# git subtree, or in its one place
#sys.path.append(filepath + '/' + 'modules/comps')
sys.path.append(filepath + '/' + '../../comps')

import fcfun   # import my functions for freecad. FreeCad Functions
import kcomp   # import material constants and other constants
import comps   # import my CAD components
import parts   # import my CAD components to print

from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, fillet_len
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL

def str_neg (num, p=0, n=0):
    """ Just a function to have the names of componentes when using for
    to differenciate them if the index is negative. FreeCAD name cannot
    have negative, so writting a 'n' instead of a '-'
    
    Parameters:
    ----------
    num : int
        the number (index of a for loop)
    p : int
        0: doesnt write a p when number is positive
        1: writes a p when number is positive
    n : int
        0: doesnt write the number, just the n or p (if p=1)
        1: writes the number, and the n if the case (or p)
    """

    if num < 0:
       if n == 0: # dont write the number
           return 'n'
       else: # write the number
           return 'n' + str(abs(num))
    else: # positive
       if n == 0: # dont write the number
           if p == 0:
               return ''
           else: # write the p, not the number
               return 'p'
       else: # write the number
           if p == 0:
               return str(num)
           else: # write the p and the number
               return 'p' + str(num)



# Taking the same axis as the 3D printer:
#
#    Z   Y
#    | /               USING THIS ONE
#    |/___ X
# 
# centered on the cubes and the vertical line of the camera and the objective
#
# as seen from the front
# be careful because at the beginning I was considering:
#      Z
#      |
#      |___ Y       NOT USING THIS ONE
#     /
#    / X
#
# In this design, the bas will be centered on X

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

doc = FreeCAD.newDocument()

Gui.ActiveDocument = Gui.getDocument(doc.Label)
guidoc = Gui.getDocument(doc.Label)


# file to save the components and their dimensions. Kind of a BOM,
# bill of materials
file_comps = open ('geo_bom.txt', 'w')

tot_d = 1000 #largo (profundidad interna)
tot_w = 800 #ancho
alu_w = 30 # ancho de los perfiles

alu_len_d = tot_d + 2 * alu_w  #perfiles a lo largo (profundo)
alu_len_v = 100  #perfiles a lo alto REVISAR
alu_len_w = tot_w #perfiles a lo ancho
alu_len_w_int = tot_w -  2 * alu_w #perfiles a lo ancho interiores

# carriage width (length=
#2: each side. 4: to have a double profile and a double bracket
alu_car_l = tot_w + 2*4*alu_w #2: each side. 4: to have a double profile and 

carro_color = fcfun.ORANGE_08
d_color = fcfun.GREEN_07
w_color = fcfun.BLUE_07

d_alu = kcomp.ALU_PROF[alu_w]

# zero in the Y of motor leadscrew support, centered on Y
# Z on top of the aluminum profiles
pos_0_x = 0.
pos_0_y = 0.
pos_0_z = 0.

pos_0 = FreeCAD.Vector(pos_0_x, pos_0_y, pos_0_z)

rod_d = 20. #diameter of the rods

leadscrew_tot_l = 500.
leadscrew_d = 16. # or 12.

alu_tray_name = 'alu_tray'

print ('travesanos ancho: ', str(alu_len_w))
# los travesanos en direccion x, cubren el ancho
for y_i in [0,1]:  # 
    alu_name = 'alu_travesano_base' + '_y' + str(y_i)
    alu_base_traves_pos = pos_0 + DraftVecUtils.scale(VY, y_i*(alu_len_d+alu_w))
    h_alu = comps.getaluprof_dir(d_alu, length=alu_len_w,
                                 fc_axis_l = VX,
                                 fc_axis_w = VY,
                                 fc_axis_p = VZN,
                                 ref_l = 1, # centered
                                 ref_w = 1, # centered
                                 ref_p = 2, # at top
                                 wfco = 1,
                                 pos = alu_base_traves_pos,
                                 name = alu_name)

    # soportes de ejes
    for x_i in [-1,1]:  # izquierda y derecha
        sh_pos = alu_base_traves_pos + DraftVecUtils.scale(VX, x_i*tot_w/2) 
        sh_name = 'sh_' + '_y' + str(y_i) + '_x' + str_neg(x_i)
        h_sh8 = comps.Sk_dir(size=rod_d,
                             fc_axis_h = VZ,
                             fc_axis_d = VY,
                             fc_axis_w = DraftVecUtils.scale(VXN,x_i),
                             ref_hr = 0,
                             ref_wc = -1, #at the end
                             ref_dc = 1,
                             tol=0, # not to print
                             pos=sh_pos,
                             name = sh_name)

# travesano interno para el final del husillo y su soporte
alu_base_traves_int_pos = pos_0 + DraftVecUtils.scale(VY, leadscrew_tot_l)
h_alu = comps.getaluprof_dir(d_alu, length=alu_len_w_int,
                                 fc_axis_l = VX,
                                 fc_axis_w = VY,
                                 fc_axis_p = VZN,
                                 ref_l = 1, # centered
                                 ref_w = 1, # centered
                                 ref_p = 2, # at top
                                 wfco = 1,
                                 pos = alu_base_traves_int_pos,
                                 name = 'travesano_int')


file_comps.write('perfiles de la base y mesa 30x30 \n')
file_comps.write('4 x ' + str(alu_len_w) + ' \n')
file_comps.write('      perfil interno soporte husillo \n')
file_comps.write('2 x ' + str(alu_len_w_int) + ' \n')

# height of the axis, from pos_0
axis_h = h_sh8.axis_h

# distance from the side to the center of the SH
axis_cen_w = h_sh8.tot_w/2

axis_len = alu_len_d + 2*alu_w


#dictionary of the linear bearing housing
d_linbear_house = kcomp.SCE20UU_Pr30b

print ('largeros: largo: ', str(alu_len_d))
# los largueros en direccion y, cubren la profundidad (depth)
for x_i in [-1,1]:  # izquierda y derecha
    alu_name = 'alu_largo_base' + '_x' + str_neg(x_i)
    alu_base_largo_pos = (pos_0 + DraftVecUtils.scale(VX, x_i*tot_w/2) 
                             + DraftVecUtils.scale(VY, alu_w/2) )

    h_alu = comps.getaluprof_dir(d_alu, length=alu_len_d,
                                 fc_axis_l = VY,
                                 fc_axis_w = DraftVecUtils.scale(VXN,x_i),
                                 fc_axis_p = VZN,
                                 ref_l = 2, # from the side
                                 ref_w = 2, # from the side
                                 ref_p = 2, # at top
                                 wfco = 1,
                                 pos = alu_base_largo_pos,
                                 name = alu_name)

    # ejes
    axis_pos = (pos_0 + DraftVecUtils.scale(VX, x_i*(tot_w/2-axis_cen_w)) 
                      + DraftVecUtils.scale(VY, -alu_w/2)
                      + DraftVecUtils.scale(VZ, axis_h)  )
    shp_rod = fcfun.shp_cyl_gen(r = rod_d/2., h=axis_len,
                              axis_h = VY,
                              pos_h = 1,
                              pos = axis_pos)
    Part.show(shp_rod)

    for y_i in [0,1]:  # 
        # Para uno de 4, todos en una pieza
        #linbear_pos_y DraftVecUtils.scale(VY,3*alu_w + y_i*alu_w)
        linbear_pos_y = DraftVecUtils.scale(VY,3*alu_w + y_i*3*alu_w)
        linbear_pos  = axis_pos + linbear_pos_y
        h_linbear_house = parts.LinBearHouse(d_linbear_house,
                                             fc_slide_axis = VY,
                                             fc_bot_axis=VZ,
                                             axis_center = 1,
                                             mid_center = 1,
                                             pos = linbear_pos)
        # height of the base of the aluminum profile of carriage, from pos_0


        alu_carr_trav_h = kcomp.SCE20UU_Pr30b['axis_h']

        # perfiles del carro

        if x_i == 1:
            alu_car_name = 'alu_car'
            for it_y in [-1,0]: # a double profile
                alu_car_y  = (pos_0 +  DraftVecUtils.scale(VZ, axis_h)
                 + linbear_pos_y +
                + DraftVecUtils.scale(VZ, alu_carr_trav_h)
                + DraftVecUtils.scale(VY,it_y*d_linbear_house['bolt_sep_l']))
               
                h_alu = comps.getaluprof_dir(d_alu, length=alu_car_l,
                                             fc_axis_l = VX,
                                             fc_axis_w = VY,
                                             fc_axis_p = VZ,
                                             ref_l = 1, # centered
                                             ref_w = 1, # centered
                                             ref_p = 2, # at bottom
                                             wfco = 1,
                                             pos = alu_car_y,
                                             name = alu_car_name)
                h_alu.color(carro_color)

                

min_mesa_h = axis_h + alu_carr_trav_h + alu_w
print('altura entre perfil de la base (top) y perfil del carro (top): ')
print(str(min_mesa_h), '\n')
            
# para tenerlo en la siguiente decena más alta, y con minimo 2 mm
mesa_h = 10* math.ceil((min_mesa_h +2) / 10.)
if (mesa_h - min_mesa_h) > 15:
    mesa_h = mesa_h - 10
print (str(mesa_h))



file_comps.write('4 x ' + str(alu_len_d) + '\n')
file_comps.write('perfiles del carro 2x30x30 (dobles) \n')
file_comps.write('2 x ' + str(alu_car_l) + '\n')

file_comps.write('altura entre perfil de la base (top) y perfil de carro (top): ')
file_comps.write(str(min_mesa_h) + '\n')

file_comps.write('perfiles elevacion mesa 30x30 \n')
file_comps.write('10 x ' + str(mesa_h) + '\n')

for x_i in [-1,1]:  # izquierda y derecha
   for y_i in [0,1]:  #delante y detras
       pos_alu_v = (pos_0 + DraftVecUtils.scale(VY, y_i*(alu_len_d+alu_w))
                         + DraftVecUtils.scale(VX, x_i*(tot_w/2-2*axis_cen_w))) 
       h_alu_v = comps.getaluprof_dir(d_alu, length=mesa_h,
                                   fc_axis_l = VZ,
                                   fc_axis_w = DraftVecUtils.scale(VXN,x_i),
                                   fc_axis_p = VY,
                                   ref_l = 2, # at bottom
                                   ref_w = 2, # at the end
                                   ref_p = 1, # centered
                                   wfco = 1,
                                   pos = pos_alu_v,
                                   name = 'alu_v')


for y_i in [0,1]:  # 
    alu_name = 'alu_travesano_mesa' + '_y' + str(y_i)
    alu_base_traves_pos = (pos_0
                           + DraftVecUtils.scale(VY, y_i*(alu_len_d+alu_w))
                           + DraftVecUtils.scale(VZ,mesa_h))
    h_alu = comps.getaluprof_dir(d_alu, length=alu_len_w,
                                 fc_axis_l = VX,
                                 fc_axis_w = VY,
                                 fc_axis_p = VZ,
                                 ref_l = 1, # centered
                                 ref_w = 1, # centered
                                 ref_p = 2, # at top
                                 wfco = 1,
                                 pos = alu_base_traves_pos,
                                 name = alu_name)


for x_i in [-1,1]:  # izquierda y derecha
    alu_name = 'alu_largo_mesa' + '_x' + str_neg(x_i)
    alu_mesa_largo_pos = (pos_0 + DraftVecUtils.scale(VX, x_i*tot_w/2) 
                             + DraftVecUtils.scale(VY, alu_w/2) 
                           + DraftVecUtils.scale(VZ,mesa_h))

    h_alu = comps.getaluprof_dir(d_alu, length=alu_len_d,
                                 fc_axis_l = VY,
                                 fc_axis_w = DraftVecUtils.scale(VXN,x_i),
                                 fc_axis_p = VZ,
                                 ref_l = 2, # from the side
                                 ref_w = 2, # from the side
                                 ref_p = 2, # at top
                                 wfco = 1,
                                 pos = alu_mesa_largo_pos,
                                 name = alu_name)


file_comps.close()

doc.recompute()

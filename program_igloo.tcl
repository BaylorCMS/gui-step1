# Microsemi Tcl Script
# flashpro
# Date: Tue Oct 11 09:37:47 2016
# Directory C:\Users\hcaldaq\gui-step1
# File C:\Users\hcaldaq\gui-step1\program_igloo.tcl
open_project -project {C:/Users/hcaldaq/gui-step1/HB_igloo/HB_igloo.pro} -connect_programmers 1
enable_prg_type -prg_type FP4 -enable FALSE
enable_prg -name 86103 -enable TRUE
set_programming_file -file {C:/Users/hcaldaq/gui-step1/HB_igloo/fixed_HB_RM_v1_03.stp}
set_programming_action -action PROGRAM
set_main_log_file -file flashpro.log
run_selected_actions
save_log -file flashpro.log
close_project

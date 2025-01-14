%% intro to syringe pump calculations
% basic linear transmission and notes on specific details. 
%
%
%
% cdeister@brown.edu
% 6/1/2018
%
%
%% a key variable is the amount of threads per mm your rod has "pitch"
%
%
% I've been opting for very standard single threaded rods as opposed to the
% elaborate multi-start rods popular on 3d printers.
%
% I have been using M8-1.25 rods, that means 8mm in diameter and 1.25 mm
% per turn. I think M8-1.0 would be better, but 1.25 works well.

rod.pitch = 1.25;

%% other key variables are diameter and length of syringe
%
% i looked up some standards (in mm)
syringe_10ml.diameter = 15.9;
syringe_10ml.length = 85.3;
syringe_10ml.volume = 10;
%
% we are going to translate linear motion into fluid transmission
% so we need to subdivide our liquid volume into the amount we would get
% for each mm of push on the cylinder
syringe_10ml.volumePerMM = syringe_10ml.volume/syringe_10ml.length;
% 117.2 ul per mm
%% now we deal with motor variables
%
% stepper motors come as 200 or 400 steps/rev (1.8 or 0.9 degrees per step
% respectivley)
%
motor.highRes_stepsPerRevoultion = 400;
motor.lowRes_stepsPerRevoultion = 200;

% microstepping.
% why microstep? we want to be able to make tiny, but still precise, steps
% to deliver real small volumes of liquid etc. if we just take the 400
% steps the motor gives us we get:
%
% we know the amount of liquid we dispense each time we push a mm on the
% syringe (117.2 ul for a 10 ml syringe) the variable above is
% "syringe_10ml.volumePerMM" so we just divide that by the step number
% (without microsteps) our chosen motor has:
%
dispense.volPerRevolution = syringe_10ml.volumePerMM * rod.pitch
dispense.volPerStep = dispense.volPerRevolution/motor.highRes_stepsPerRevoultion
%
% for a 10 ml syringe and a 400 step motor, we get 0.000366 ml (366 nl) per
% full step. This is reasonable for a reward, but we can't really control
% the physics of a single step. There is no way to model acceleration or
% decceleration to overcome the initial stop-cock load etc. 
%
% FYI we could get a finer rod, M8 specs down to 0.75 pitch:
%
dispense.volPerRevolution_fine = syringe_10ml.volumePerMM * 0.75
dispense.volPerStep_fine = dispense.volPerRevolution_fine/motor.highRes_stepsPerRevoultion
%
% This gives 219.81 ul per step, which isn't crazy better.
% ~~~~~~
% ~~~~~~~~ mic ~~~
% ~~~~~~~~~~~~ ro ~~~
% ~~~~~~~~~~~~~~~~ stepping ~~~
%
% let's go back to our actual rod pitch of 1.25 etc. and see what
% microstepping does. 
%
% We can't do better than the resolution of microstepping the driver
% allows. For most it is 128 and for the trinamic drivers it is 256. 
motor.microstepResolution = 256;
dispense.volPerMicrostep= dispense.volPerStep / motor.microstepResolution;
% Thus, we take a 331 nl drop and potentially can make it 1/256th of that
% and get 0.00000143 ml; or 1.43 nl. However, toqrue gets more variable as
% we chop up a full step. In general, for 128 microstepping drivers, across
% many conditions, the lore is 1/16th stepping is the boundary. 

% To get 1/16th of a full step with 256 resolution; you take 256/16, which
% happens to be 16. So 16 microsteps will be 1/16th of a full step. For
% 1/32 it's 256/32 or 8 microsteps per division. 

dispense.volPer16th = dispense.volPerMicrostep * 16;
dispense.volPer32nd = dispense.volPerMicrostep * 8


% Which is 22.9 nl or 11.44 nl, respectivley.

% I've set csDashboard to start with a bolus of 1600 microsteps; which
% would be 100 1/16th steps. This will give 
dispense.defaultBolusSize = 1600;
dispense.volPerBolus_default = dispense.defaultBolusSize * dispense.volPerMicrostep
% This gives 2.3 ul per reward. 
% you can go down to 16 steps without losing torque, but you lose some
% ability to control acceleration etc.
% By default, csDashboard will move in 800 step increments, so if you go to
% the 800 you will get a 1.15 ul drop. 
% I will set the default increment to be 160 instead of 800




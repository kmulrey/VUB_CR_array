# Copyright (C) 2018 Pico Technology Ltd. See LICENSE file for terms.
#
# PS2000A BLOCK MODE EXAMPLE
# This example opens a 2000a driver device, sets up one channels and a trigger then collects a block of data.
# This data is then plotted as mV against time in ns

import os
import time
import ctypes
import numpy as np
from datetime import datetime
from picosdk.ps2000a import ps2000a as ps
from picosdk.functions import adc2mV, mV2adc, assert_pico_ok

# Which voltage do you want for your trigger(s)
triggerVoltage = 500 # [mV]

# Setting the number of samples to be collected
preTriggerFraction = 0.3
samples = int(1E6)
# samples = preTriggerSamples + postTriggerSamples
preTriggerSamples = int( samples * preTriggerFraction )
postTriggerSamples = samples - preTriggerSamples

# First, we are going to create the folder if it isn't there already
# The external drive folder
mydir = /mnt/extdrive
mydir = os.path.join( mydir, datetime.now().strftime('%Y-%m-%d') )
#mydir = os.path.join( os.getcwd(), datetime.now().strftime('%Y-%m-%d'))
if not os.path.isdir(mydir): os.makedirs(mydir)

# Create handle and status ready for use
status = {}
handle = ctypes.c_int16()       # Actually c-handle

# Opens the device
status["openunit"] = ps.ps2000aOpenUnit(ctypes.byref(handle), None)

try:
    assert_pico_ok(status["openunit"])
except:

    # powerstate becomes the status number of openunit
    powerstate = status["openunit"]

    # If powerstate is the same as 282 then it will run this if statement
    if powerstate == 282:
        # Changes the power input to "PICO_POWER_SUPPLY_NOT_CONNECTED"
        status["ChangePowerSource"] = ps.ps2000aChangePowerSource(handle, 282)
        # If the powerstate is the same as 286 then it will run this if statement
    elif powerstate == 286:
        # Changes the power input to "PICO_USB3_0_DEVICE_NON_USB3_0_PORT"
        status["ChangePowerSource"] = ps.ps2000aChangePowerSource(handle, 286)
    else:
        raise

    assert_pico_ok(status["ChangePowerSource"])

# Sets timebase (time interval)
timebase = 1                            # It should be 1, the smallest timebase possible for 2 channels
segmentIndex = 0                        # This is meant for when the pico memory is split (rapid block)
timeIntervalns = ctypes.c_float()       # Return info
maxSamples = ctypes.c_int32()           # Return info
status["GetTimebase"] = ps.ps2000aGetTimebase2(handle, timebase, samples, ctypes.byref(timeIntervalns), 1, ctypes.byref(maxSamples), segmentIndex)
assert_pico_ok(status["GetTimebase"])

print( "The time step between samples is " + str(timeIntervalns) )
print( "The maximum amount of samples in this configuration is" + str(maxSamples.value) )
print( "The requested amount for samples per event is: " + str(samples))

# Find the max ADC count (For the ADC <-> mV conversion)
# This is obtained from the PicoScope itself
maxADC = ctypes.c_int16()
status["maximumValue"] = ps.ps2000aMaximumValue(handle, ctypes.byref(maxADC))
assert_pico_ok(status["maximumValue"])

# Set up channels

# A
enableA = 1     # Turn on (1) or off (0)
channelA = 0    # PS2000A_CHANNEL_A
couplingA = 1   # coupling type: PS2000A_DC = 1
rangeA = 7
offsetA = 0     # analogue offset
"""
The pico 2206B ranges
0 = PS2000A_20MV:  ±20 mV
1 = PS2000A_50MV:  ±50 mV
2 = PS2000A_100MV: ±100 mV
3 = PS2000A_200MV: ±200 mV
4 = PS2000A_500MV: ±500 mV
5 = PS2000A_1V
6 = PS2000A_2V
7 = PS2000A_5V
8 = PS2000A_10V
9 = PS2000A_20V
"""

status["setChA"] = ps.ps2000aSetChannel(handle, channelA, enableA, couplingA, rangeA, offsetA)
assert_pico_ok(status["setChA"])

# B
enableB = 1     # Turn on (1) or off (0)
channelB = 1    # PS2000A_CHANNEL_B
couplingB = 1   # coupling type: PS2000A_DC = 1
rangeB = 7
offsetB = 0     # analogue offset

status["setChB"] = ps.ps2000aSetChannel(handle, channelB, enableB, couplingB, rangeB, offsetB)
assert_pico_ok(status["setChB"])

# Set the trigger
adcTriggerLevel = mV2adc(triggerVoltage, rangeA, maxADC)

    # Trigger channel properties
channelAProperties = ps.PS2000A_TRIGGER_CHANNEL_PROPERTIES(
    adcTriggerLevel,      # Upper threshold
    10,                   # Threshold's Hysteresis
    adcTriggerLevel,      # Lower threshold
    10,
    ps.PS2000A_CHANNEL["PS2000A_CHANNEL_A"],
    ps.PS2000A_THRESHOLD_MODE["PS2000A_LEVEL"]  # LEVEL = THRESHOLD or WINDOW

)

channelBProperties = ps.PS2000A_TRIGGER_CHANNEL_PROPERTIES(
    adcTriggerLevel,      # Upper threshold
    10,                   # Threshold's Hysteresis
    adcTriggerLevel,      # Lower threshold
    10,
    ps.PS2000A_CHANNEL["PS2000A_CHANNEL_B"],
    ps.PS2000A_THRESHOLD_MODE["PS2000A_LEVEL"]  # LEVEL = THRESHOLD or WINDOW
)

    # Make those into a C compatible array
channelProperties = []
channelProperties.append(channelAProperties)
channelProperties.append(channelBProperties)
cProperties = (ps.PS2000A_TRIGGER_CHANNEL_PROPERTIES * len(channelProperties))(*channelProperties)  # This line is just #Magic

# nChannelProperties = len(channelProperties)
# auxOutputEnabled = 0      # There is no auxOutput
autoTriggerMilliseconds = 0 # If there is no trigger, trigger after X ms. 0 = disable.

status["setTrigProp"] = ps.ps2000aSetTriggerChannelProperties(handle, ctypes.byref(cProperties), len(channelProperties), 0, autoTriggerMilliseconds)
assert_pico_ok(status["setTrigProp"])

    # Trigger directions
channelADirection = ps.PS2000A_THRESHOLD_DIRECTION["PS2000A_FALLING"]
channelBDirection = ps.PS2000A_THRESHOLD_DIRECTION["PS2000A_FALLING"]
channelCDirection = ps.PS2000A_THRESHOLD_DIRECTION["PS2000A_NONE"]
channelDDirection = ps.PS2000A_THRESHOLD_DIRECTION["PS2000A_NONE"]
extDirection      = ps.PS2000A_THRESHOLD_DIRECTION["PS2000A_NONE"]
auxDirection      = ps.PS2000A_THRESHOLD_DIRECTION["PS2000A_NONE"]
status["setTrigDir"] = ps.ps2000aSetTriggerChannelDirections(handle, channelADirection, channelBDirection, channelCDirection, channelDDirection, extDirection, auxDirection)
assert_pico_ok(status["setTrigDir"])

    # Trigger conditions
"""
Trigger conditions
The final trigger is the OR of all elements in this array, where all the
conditions within an element are AND. Our case is 1 element array of conditions
A AND B.
"""
conditions = ps.PS2000A_TRIGGER_CONDITIONS(
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_TRUE"],
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_TRUE"],
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_DONT_CARE"],
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_DONT_CARE"],
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_DONT_CARE"],
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_DONT_CARE"],
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_DONT_CARE"],
    ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_DONT_CARE"]
)

nConditions = 1
status["setTrigCond"] = ps.ps2000aSetTriggerChannelConditions(handle, ctypes.byref(conditions), nConditions)
assert_pico_ok(status["setTrigCond"])

# Set Singal Generator / Trigger Out
# Outputs a square wave with peak-to-peak voltage (amplitude) of 1 V and frequency of 1 MHz

offsetVoltage = int(5E5)            # [uV], the channel out has a -0.5V potential
pkpk = int(1E6)                     # [uV]
wavetype = ctypes.c_int16(1)        # = PS2000A_SQUARE
"""
0 = PS2000A_SINE
1 = PS2000A_SQUARE
...
"""
startFrequency = int(1E6)           # [Hz]
stopFrequency  = int(1E6)           # [Hz]
# increment = 0                     # sweep: Change between steps
# dwellTime = 0                     # [s] sweep: Time per step
# sweepType = ctypes.c_int16(0)     # sweep mode: Up, down, updown, downup
# operation = 0                     # Extra operations: 0 = OFF, PS2000A_WHITENOISE, PS2000A_PRBS (pseudo random binary sequence)
shots = 1                           # Number of pulse cycles per trigger call
sweeps = 0                          # Number of sweeps: 0  [ctypes.c_int32(0)] = OFF [shots]
triggertype = 0                     # Trigger Type Rising
triggerSource = 1                   # None, PS2000A_SIGGEN_SOFT_TRIG
# extInThreshold                    # Not applicable

status["SetSigGenBuiltIn"] = ps.ps2000aSetSigGenBuiltIn(handle, offsetVoltage, pkpk, wavetype,
        startFrequency, stopFrequency, 0, 0, 0, 0, shots, sweeps, triggertype, triggerSource, 0)
assert_pico_ok(status["SetSigGenBuiltIn"])

print("Picoscope Ready")

# We are going to prepare the readout system

# This first part can be prepared in advance, but we have no guarantee that
# for every event the buffer is fully overwritten by GetDataValues.
# This could also happen within the loop according to manual.

# Create buffers ready for data collection
# channelA = 0, as before
# channelB = 1, as before
# Buffer length = samples
# Downsamling Ratio mode: None = 0

bufferA = (ctypes.c_int16 * samples)()
status["SetDataBuffer"] = ps.ps2000aSetDataBuffer(handle, channelA, ctypes.byref(bufferA), samples, segmentIndex, 0)
assert_pico_ok(status["SetDataBuffer"])

bufferB = (ctypes.c_int16 * samples)()
status["SetDataBuffer"] = ps.ps2000aSetDataBuffer(handle, channelB, ctypes.byref(bufferB), samples, segmentIndex, 0)
assert_pico_ok(status["SetDataBuffer"])

# If you want aggregation downsampling, you need to use 2 buffers: Max and Min
# status["SetDataBuffers"] = ps.ps2000aSetDataBuffers(handle, 0, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), samples, 0, 0)

# Create a buffer for overflow data
# It has to have 1 dimension per channel to mark where has ocurred overflow. 0 = A, 1 = B.
overflow = (ctypes.c_int16 * 2)()

# Start the block capture
# for i in range(1):
while(1):

    # The event time is referred to local PC time
    filename = datetime.now().strftime('%H-%M-%S')

    # preTriggerSamples, postTriggerSamples, timebase and segementIndex are set above.
    # oversample = 1 not used value.
    # time indisposed ms = None (This is not needed within the example)
    # LpRead = None             # Callback function
    # pParameter = None         # Callback parameter
    status["runblock"] = ps.ps2000aRunBlock(handle, preTriggerSamples, postTriggerSamples, timebase, 1, None, segmentIndex, None, None)
    assert_pico_ok(status["runblock"])

    # We are not going to use a callback (not implemented in python) but polling:
    # This is, check constantly is the data collection is finished to finish the capture
    ready = ctypes.c_int16(0)
    while ready.value == 0:
        status["isReady"] = ps.ps2000aIsReady(handle, ctypes.byref(ready))

    # When finished, we are going to collect our data in the buffers
    startIndex = 0      # Where you start taking samples
    # noOfSamples = ctypes.byref(csamples)
    # DownSampleRatio = 0
    # DownSampleRatioMode = 0
    # SegmentIndex = 0
    # Overflow = ctypes.byref(overflow)

    status["GetValues"] = ps.ps2000aGetValues(handle, startIndex, ctypes.byref(ctypes.c_int32(samples)), 0, 0, segmentIndex, ctypes.byref(overflow))
    assert_pico_ok(status["GetValues"])

    print("Triggered event")

    # You can check for Overflow
    if   overflow[0] != 0: print("Overrange error in Channel A for " + filename)
    elif overflow[1] != 0: print("Overrange error in Channel B for " + filename)

    # Generate the data
    time = np.linspace(0, samples * timeIntervalns.value, samples)
    mVA = adc2mV(bufferA, rangeA, maxADC)
    mVB = adc2mV(bufferB, rangeB, maxADC)

    # And then put them into a file
    with open(os.path.join(mydir, filename), 'w') as file:

        for i in range(samples):
            file.write(str(time[i]) + '\t' + str(mVA[i]) +  '\t'+ str(mVB[i]) + '\n')


# Stops the scope
# Handle = handle
status["stop"] = ps.ps2000aStop(handle)
assert_pico_ok(status["stop"])

# Closes the unit
# Handle = handle
status["close"] = ps.ps2000aCloseUnit(handle)
assert_pico_ok(status["close"])

# Displays the staus returns
print(status)

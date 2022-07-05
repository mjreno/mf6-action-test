import flopy


print("precall")
print(dir(flopy))
print(dir(flopy.mf6))
fp = flopy.mf6.__init__('fp')
sim = flopy.mf6.MFSimulation(
            sim_name='sim', version="mf6", exe_name='mf6', sim_ws='./ws'
        )
print("postcall")

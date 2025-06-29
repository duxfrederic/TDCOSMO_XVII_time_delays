#####################
#  Configuration file
#####################
import sys
import pycs3.spl.topopt
import pycs3.regdiff.multiopt
import pycs3.gen.polyml
import pycs3.gen.splml
import numpy as np
import pycs3.pipe.pipe_utils as ut

#info about the lens :
full_lensname =''
lcs_label = ['A','B','C','D']
delay_labels = ['AB', 'AC', 'AD', 'BC', 'BD', 'CD']
#PLACEHOLDERLCLABELS
#PLACEHOLDERDELAYLABELS
#initial guess :
timeshifts = ut.convert_delays2timeshifts([0.,0.,0.])#give the estimated AB delay
#PLACEHOLDERTIMESHIFTS
magshift = None # if None, we remove the median magnitude of each curve

#general config :
askquestions = False
display = False
max_core = None #None will use all the core available


### OPTIMISATION FUNCTION ###
# select here the optimiser you want to use :
optfctkw = "spl1" #function you used to optimise the curve at the 1st plase (in the script 2a), it should stay at spl1
simoptfctkw = "spl1" #function you want to use to optimise the mock curves, currently support spl1 and regdiff

### SPLINE PARAMETERS ###
knotstep = [15,25,35,45] #give a list of the parameter you want

### REGDIFF PARAMETERS ###
#To use 5 set of parameters pre-selected :
use_preselected_regdiff = True #highly recommended, set to True
preselection_file = 'scripts/config/preset_regdiff.txt'
#You can give your own grid here if use_preselected_regdiff == False :
covkernel = ['matern']  # can be matern, RatQuad or RBF
pointdensity = [2]
pow = [2.5]
errscale = [1.0]


### RUN PARAMETERS #####
#change here the number of copie and mock curve you want to draw :
# copies
ncopy = 20 #number of copy per pickle
ncopypkls = 25 #number of pickle

# mock
nsim = 20 #number of copy per pickle
nsimpkls = 40 #number of pickle
truetsr = 10.0  # Range of true time delay shifts when drawing the mock curves
tsrand = 10.0  # Random shift of initial condition for each simulated lc in [initcond-tsrand, initcond+tsrand]

## sim
run_on_copies = True
run_on_sims = True


### MICROLENSING ####
mltype = "splml"  # splml or polyml
mllist = [0,1,2,3]  # Which lcs do you want to attach ml to ?
mlname = 'splml'
mlknotsteps = [150,300,450,600]# 0 means no microlensing...
#To force the spacing  :
forcen = True # if true I doesn't use mlknotstep
nmlspl = [0,1,2,3]  #nb_knot - 1, used only if forcen == True, 0, means no microlensing
#mlbokeps = 88 #  min spacing between ml knots, used only if forcen == True

#polyml parameters :
degree = [0,1,2,3,4] # degree - 1, used only if mltype = "polyml",  0, means no microlensing


###### TWEAK ML #####
#Noise generator for the mocks light curve, script 3a :
tweakml_name = 'PS' #give a name to your tweakml, change the name if you change the type of tweakml, avoid to have _opt_ in your name !
tweakml_type = 'PS_from_residuals' #choose either colored_noise or PS_from_residuals
shotnoise_type = None #Select among [None, "magerrs", "res", "mcres", "sigma"] You should have None for PS_from_residuals

find_tweak_ml_param = True #To let the program find the parameters for you, if false it will use the lines below :
colored_noise_param = [[-2.95,0.001],[-2.95,0.001],[-2.95,0.001],[-2.95,0.001]] #give your beta and sigma parameter for colored noise, used only if find_tweak_ml == False
PS_param_B = [[1.0],[1.0],[1.0],[1.0]] #if you don't want the algorithm fine tune the high cut frequency (given in unit of Nymquist frequency)

#if you chose to optimise the tweakml automatically, you might want to change this
optimiser = 'DIC' # dichotomic optimiser, only DIC is available for the moment
n_curve_stat =16# Number of curve to compute the statistics on, (the larger the better but it takes longer... 16 or 32 are good, 8 is still OK) .
max_iter = 15 # this is used in the DIC optimiser, 10 is usually enough.


###### SPLINE MARGINALISATION #########
# Chose the parameters you want to marginalise on for the spline optimiser. Script 4b.
name_marg_spline = 'marginalisation_spline'  # choose a name for your marginalisation
tweakml_name_marg_spline = ['PS']
knotstep_marg = knotstep  # parameters to marginalise over, give a list or just select the same that you used above to marginalise over all the available parameters
if forcen and mltype == 'splml':  # microlensing parameters to marginalise over, give a list or just select the same that you used above to marginalise over all the available parameters
	mlknotsteps_marg = nmlspl
elif mltype == 'splml':
	mlknotsteps_marg = mlknotsteps
elif mltype == 'polyml':
	mlknotsteps_marg = degree
else:
	mlknotsteps_marg = []

###### REGDIFF MARGINALISATION #########
# Chose the parameters you want to marginalise on for the regdiff optimiser. Script 4c.
# We will marginalise over the set of parameters in your preselection_file, you have to create one at this step.
name_marg_regdiff = 'marginalisation_regdiff'
tweakml_name_marg_regdiff = ['PS']
knotstep_marg_regdiff = knotstep  # choose the knotstep range you want to marginalise over, by default it is recommanded to take the same as knotstep
if forcen and mltype == 'splml':  # microlensing parameters to marginalise over, give a list or just select the same that you used above to marginalise over all the available parameters
	mlknotsteps_marg_regdiff = nmlspl
elif mltype == 'splml':
	mlknotsteps_marg_regdiff = mlknotsteps
elif mltype == 'polyml':
	mlknotsteps_marg_regdiff = degree
else:
	mlknotsteps_marg_regdiff = []

#other parameteres for regdiff and spline marginalisation :
testmode = True # number of bin to use for the mar
sigmathresh = 0.5   #sigma threshold for sigma clipping, 0 is a true marginalisation, choose 1000 to take the most precise.

###### MARGGINALISE SPLINE AND REGDIFF TOGETHER #######
#choose here the marginalisation you want to combine in script 4d, it will also use the sigmathresh:
name_marg_list = ['marginalisation_spline','marginalisation_regdiff']
display_name = ['Free-knot Spline', 'Regression Difference']
new_name_marg = 'marginalisation_final'
sigmathresh_list = [0.5,0.5] #sigmathresh to use for marginalisation_spline and marginalisation_regdiff, it can be different from the sigmathresh used for the new marginalisation
sigmathresh_final = 0.0 #sigma used in the final marginalisation

### Functions definition
def spl1(lcs, **kwargs):
	# spline = pycs3.spl.topopt.opt_rough(lcs, nit=5)
	# spline = pycs3.spl.topopt.opt_fine(lcs, knotstep=kwargs['kn'], bokeps=kwargs['kn']/3.0, nit=5, stabext=100)
	kn = kwargs['kn']
	spline = pycs3.spl.topopt.opt_rough(lcs, nit=1, knotstep=kn)
	# spline = pycs3.spl.topopt.opt_fine(lcs, knotstep=kwargs['kn'], bokeps=kwargs['kn']/3.0, nit=5, stabext=100)
	spline = pycs3.spl.topopt.opt_fine(lcs, nit=1, knotstep=kn, verbose=True)
	return spline

def regdiff(lcs, **kwargs):
	return pycs3.regdiff.multiopt.opt_ts(lcs, pd=kwargs['pointdensity'], covkernel=kwargs['covkernel'], pow=kwargs['pow'],
										 errscale=kwargs['errscale'], verbose=True, method="weights")


###### DON'T CHANGE ANYTHING BELOW THAT LINE ######
def attachml_single(lc, ml):

    if ml == "None" : #I do nothing if there is no microlensing to attach.
        # 2022-06-09: there is a bug in PyCS, the optimization of the offset is not done properly.
        # thus add a polynomial of order 0
        pycs3.gen.polyml.addtolc(lc,  nparams=1, autoseasonsgap=1000)
        return
    elif ml == "linear":
        pycs3.gen.polyml.addtolc(lc,  nparams=2, autoseasonsgap=1000)
        return
    elif ml == "quadratic":
        pycs3.gen.polyml.addtolc(lc,  nparams=3, autoseasonsgap=1000)
        return
    elif ml == "cubic":
        pycs3.gen.polyml.addtolc(lc,  nparams=4, autoseasonsgap=1000)
        return
    elif ml == "spline_3_fixed_knot":
        # this is the case where we want a single internal knot, and also want it fixed in the middle.
        curve_length = lc.jds[-1] - lc.jds[0]
        mlbokeps = np.floor(curve_length / 2.) - 1   # epsilon (min distance betwen knots) set to about half the curve, i.e. forced in the middle
        pycs3.gen.splml.addtolc(lc, n=2, bokeps=mlbokeps)
    elif ml == "spline_3":
        # this is the case where we want a single internal knot, free to move
        curve_length = lc.jds[-1] - lc.jds[0]
        mlbokeps = np.floor(curve_length / 10.)  # smaller epsilon for more freedom.
        pycs3.gen.splml.addtolc(lc, n=2, bokeps=mlbokeps)
    elif ml.startswith("spline_"):
        order = int(ml.split('_')[1])
        curve_length = lc.jds[-1] - lc.jds[0]
        mlbokeps = np.floor(curve_length / (10.+order))  # smaller epsilon for more freedom.
        pycs3.gen.splml.addtolc(lc, n=order-1, bokeps=mlbokeps)
    else:
        raise NotImplementedError(ml)

def attachml(lcs, mls):
    if not type(mls) == list:
        mls = len(lcs) * [mls]
    else:
        assert len(mls) == len(lcs)
    for lc, ml in zip(lcs, mls):
        attachml_single(lc, ml)
		
		
def attachml_old(lcs, ml):
	if ml == 0 : #I do nothing if there is no microlensing to attach.
		# 2022-06-09: there is a bug in PyCS, the optimization of the offset is not done properly.
		# thus add a polynomial of order 0
		for lc in lcs : 
			pycs3.gen.polyml.addtolc(lc,  nparams=1, autoseasonsgap=1000)
		return
	elif ml == 1.5:
		for lc in lcs : #spline cannot have 0 internal knot, then we use a polynome of degree 2 to represents a spline with only two external knot
			pycs3.gen.polyml.addtolc(lc,  nparams=3, autoseasonsgap=1000)
	lcmls = [lcs[ind] for ind in mllist]
	mlvec = [ml for ind in mllist] # this is either the number of knot, either a knot step depending if forcen is True or False
	if mltype == 'splml':
		if forcen:
			for lcml, nml in zip(lcmls, mlvec):
				curve_length = lcml.jds[-1] - lcml.jds[0]
				mlbokeps = np.floor(curve_length / nml)

				if nml == 1 : #spline cannot have 0 internal knot, then we use a polynome of degree 2 to represents a spline with only two external knot
					pycs3.gen.polyml.addtolc(lcml,  nparams=3 )
				else :
					pycs3.gen.splml.addtolc(lcml, n=nml, bokeps=mlbokeps)
		else:
			for lcml, mlknotstep in zip(lcmls, mlvec):
				mlbokeps_ad = mlknotstep / 3.0   #maybe change this
				pycs3.gen.splml.addtolc(lcml, knotstep=mlknotstep, bokeps=mlbokeps_ad)

	# polynomial microlensing
	nparams = [ml for ind in mllist]
	if mltype == 'polyml':
		for ind, lcml in enumerate(lcmls):
			pycs3.gen.polyml.addtolc(lcml, nparams=nparams[ind], autoseasonsgap=600.0)

if optfctkw == "spl1":
	optfct = spl1
	splparamskw = ["ks%i" %knotstep[i] for i in range(len(knotstep))]

if optfctkw == "regdiff": # not used, small haxx to be able to execute 2 to check and 3 using the spl1 drawing
	optfct = regdiff
	splparamskw = "ks%i" % knotstep

if simoptfctkw == "spl1":
	simoptfct = spl1

if simoptfctkw == "regdiff":
	simoptfct = regdiff
	if use_preselected_regdiff :
		regdiffparamskw = ut.read_preselected_regdiffparamskw(preselection_file)
	else :
		regdiffparamskw = ut.generate_regdiffparamskw(pointdensity,covkernel, pow, amp)


if mltype == "splml":
    combkw = [
        [f"{optfctkw}_ks{knotstep_i}_{mlname}_knml_{mlknotstep_j}" for mlknotstep_j in mlknotsteps]
        for knotstep_i in knotstep
    ] if not forcen else [
        [f"{optfctkw}_ks{knotstep_i}_{mlname}_nmlspl_{nmlspl_j}" for nmlspl_j in nmlspl]
        for knotstep_i in knotstep
    ]
elif mltype == "polyml":
    combkw = [
        [f"{optfctkw}_ks{knotstep_i}_{mlname}_deg_{degree_j}" for degree_j in degree]
        for knotstep_i in knotstep
    ]
else:
    raise RuntimeError('I don\'t know your microlensing type. Choose "polyml" or "spml".')

combkw = np.asarray(combkw)

simset_copy = "copies_n%i" % (int(ncopy * ncopypkls))
simset_mock = "mocks_n%it%i_%s" % (int(nsim * nsimpkls), truetsr,tweakml_name)

if simoptfctkw == "regdiff":
	if use_preselected_regdiff :
		kwargs_optimiser_simoptfct = ut.get_keyword_regdiff_from_file(preselection_file)
		optset = [simoptfctkw + regdiffparamskw[i] + 't' + str(int(tsrand)) for i in range(len(regdiffparamskw))]
	else :
		kwargs_optimiser_simoptfct = ut.get_keyword_regdiff(pointdensity, covkernel, pow, errscale)
		optset = [simoptfctkw + regdiffparamskw[i] + 't' + str(int(tsrand)) for i in range(len(regdiffparamskw))]
elif simoptfctkw == 'spl1':
	optset = [simoptfctkw + 't' + str(int(tsrand))]
else :
	print('Error : I dont recognize your simoptfctkw, please use regdiff or spl1')
	sys.exit()

#!/usr/bin/python3
import sys, os

import time
from math import *
import numpy as np
import matplotlib.pyplot as plt

# import SIM5 library
sys.path.append(os.path.abspath(os.path.join(__file__, '../../../..')))
import sim5

# define black hole/system parameters
bh_mass = 10        # [solar mass]
bh_spin = 0.66      # []
bh_dist = 1e3       # [kpc]
bh_incl = 60.0      # [degrees]
bh_rms  = sim5.r_ms(bh_spin)

# read parameters from command line, if provided
if (len(sys.argv) > 2):
    bh_spin = float(sys.argv[1])
    bh_incl = float(sys.argv[2])


# define disk parameters
disk_mdot  = 0.1    # [Mdot_Edd]
disk_alpha = 0.1    # []

# define image paramaters
image_dim_x = 1280  # [pixels]
image_dim_y =  720  # [pixels]


# set up a Novikov-Thorne disk model
sim5.disk_nt_setup(bh_mass, bh_spin, disk_mdot, disk_alpha, 0)

# initialize blank image
image_f = np.zeros((image_dim_y, image_dim_x))
image_g = np.zeros((image_dim_y, image_dim_x))


# set view width of view
# (determines how big portion of the disk shall the image cover)
rmax = sim5.r_ms(bh_spin) + 15.0

print("Computing ... ", end='', flush=True)

time1 = time.time()

# go over the image and determine each pixel brightness
for iy in range(image_dim_y):
    for ix in range (image_dim_x):
        # set impact parameters
        # these are just image coordinates scaled to real dimensions of the source shifted so 
        # that [0,0] is in the middle of the image
        alpha = ((ix+.5)/image_dim_x - 0.5) * 2.0*rmax
        beta  = ((iy+.5)/image_dim_y - 0.5) * 2.0*rmax * (image_dim_y/image_dim_x)

        # setup geodesic object and a container for status
        gd = sim5.geodesic()
        error = sim5.intp()

        # initialize photon trajectory for particular impact parameters [alpha,beta] 
        # with one endpoint at infinity
        sim5.geodesic_init_inf(radians(bh_incl), bh_spin, alpha, beta, gd, error);
        if (error.value()): continue
            
        # find where the trajectory crosses equatorial plane for the first time (zero-th order crossing) 
        # and obtain geodesic position parameter P (or NaN if there is no crossing)
        P = sim5.geodesic_find_midplane_crossing(gd, 0)
        if (isnan(P)): continue

        # from the position parameter get radius from which the photon originates
        r = sim5.geodesic_position_rad(gd, P)
        if (isnan(r)): continue

        # if r<rms then the crossing lies inside the last stable orbit, 
        # where the this disk is not defined, thus radiation is zero.
        # outside of rms, determine disk radiation (f) and relativistic 
        # correction to it (g)
        if (r >= bh_rms):
            g = sim5.gfactorK(r, bh_spin, gd.l)
            f = sim5.disk_nt_flux(r)
            image_f[iy, ix] = f*pow(g,4.)
            image_g[iy, ix] = g
            # break the calculation and continue with next pixel
            continue

        # the same thing for photons that make one orbit around the black hole
        # and may bring light from the bottom side of the disk
        P = sim5.geodesic_find_midplane_crossing(gd, 1)
        if (isnan(P)): continue
        r = sim5.geodesic_position_rad(gd, P)
        if (r >= bh_rms):
            g = sim5.gfactorK(r, bh_spin, gd.l)
            f = sim5.disk_nt_flux(r)
            image_f[iy, ix] = f*pow(g,4.)
            image_g[iy, ix] = g
            continue


time2 = time.time()
print("done\n",  end='')

print("Profiling:")
print("    photons:", image_dim_x*image_dim_y)
print("    time: %.1f" % (time2-time1))     
print("    rate: %.1f" % (image_dim_x*image_dim_y/(time2-time1)), 'photons/sec')

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8,10))

ax1.set_title("Image")
ax1.imshow(image_f, origin='lower', cmap='gray')
ax1.axis('off')

ax2.set_title("g-factor map")
ax2.imshow(image_g, origin='lower', cmap='RdBu', vmin=0.5, vmax=1.3)
ax2.axis('off')

plt.show()



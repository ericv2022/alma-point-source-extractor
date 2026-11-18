"""CASA-only source fitting, extracted verbatim from APSE v0.1.0.

Scientific algorithm intentionally unchanged. Do not modify without regression.
"""
import os
import numpy as np
from casatools import image as iatool, quanta as qatool

def extractSourcesFromImage(img_sky_pbcor, img_pb, min_snr=6, fit_width=10, nmax_src=1000, zerooff_snr=3):

    myia = iatool()
    myqa = qatool()

    prefix1 = img_sky_pbcor.replace('pbcor.fits', '')

    img_sky_pbuncor = prefix1+'pbuncor.image'

    myia.open(img_sky_pbcor)
    myia.pbcor(pbimage=img_pb, outfile=img_sky_pbuncor, mode='multiply', overwrite=True)
    myia.close()

    myia.open(img_sky_pbuncor)

    img_stats = myia.statistics()
    img_peak = img_stats['max'][0]

    img_stats = myia.statistics(algorithm='chauvenet')
    img_rms = img_stats['rms'][0]

    flux_cutoff = img_rms * min_snr / img_peak
    fit_width1 = round(fit_width/2.)

    src_dict = {}

    if flux_cutoff < 1:
        src_dict = myia.findsources(nmax=nmax_src, cutoff=flux_cutoff, width=fit_width1, point=False)

    myia.close()

    src_dict2 = {}

    if len(src_dict) != 0:

        myia.open(img_sky_pbuncor)

        img_shape = myia.shape()

        for i in range(src_dict['nelements']):

            src_ra = src_dict['component'+str(i)]['shape']['direction']['m0']['value']
            src_dec = src_dict['component'+str(i)]['shape']['direction']['m1']['value']

            src_pixelpos = myia.topixel([src_ra, src_dec])

            src_dict['component'+str(i)]['pixelcoords'] = src_pixelpos['numeric']

        myia.close()

        for i in range(src_dict['nelements']):

            if 'type' in src_dict['component'+str(i)]['shape'].keys():
                if src_dict['component'+str(i)]['shape']['type'] == 'Point': continue

            peakX = src_dict['component'+str(i)]['pixelcoords'][0]
            peakY = src_dict['component'+str(i)]['pixelcoords'][1]

            if peakX < 0 or peakX > img_shape[0]-1: continue
            if peakY < 0 or peakY > img_shape[1]-1: continue

            peakI = src_dict['component'+str(i)]['flux']['value'][0]
            bMaj = src_dict['component'+str(i)]['shape']['majoraxis']['value']
            bMajUnit = src_dict['component'+str(i)]['shape']['majoraxis']['unit']
            bMin = src_dict['component'+str(i)]['shape']['minoraxis']['value']
            bMinUnit = src_dict['component'+str(i)]['shape']['minoraxis']['unit']
            bPa = src_dict['component'+str(i)]['shape']['positionangle']['value']
            bPaUnit = src_dict['component'+str(i)]['shape']['positionangle']['unit']

            with open(prefix1+'estimates.txt', 'w') as f:
                f.write(f"{peakI}, {peakX}, {peakY}, {bMaj}{bMajUnit}, {bMin}{bMinUnit}, {bPa}{bPaUnit}\n")
            f.close()

            myia.open(img_sky_pbuncor)
        
            img_shape = myia.shape()

            found = False

            fit_width1 = round(fit_width/2.)
        
            if peakX-fit_width1 > 0 and peakY-fit_width1 > 0 and peakX+fit_width1 < img_shape[0]-1 and peakY+fit_width1 < img_shape[1]-1:
        
                src_box = str(peakX-fit_width1)+','+str(peakY-fit_width1)+','+str(peakX+fit_width1)+','+str(peakY+fit_width1)
                src_dict1 = myia.fitcomponents(box=src_box, rms=img_rms, dooff=True, estimates=prefix1+'estimates.txt', logfile=prefix1+'logfile.txt')

                if src_dict1['converged'][0] == True:

                    fit_width1 = round( 3 * src_dict1['results']['component0']['shape']['majoraxis']['value'] * max(src_dict1['pixelsperarcsec']) / 2.) # convert value of 3 into an input parameter

                    if peakX-fit_width1 > 0 and peakY-fit_width1 > 0 and peakX+fit_width1 < img_shape[0]-1 and peakY+fit_width1 < img_shape[1]-1:

                        src_box = str(peakX-fit_width1)+','+str(peakY-fit_width1)+','+str(peakX+fit_width1)+','+str(peakY+fit_width1)
                        src_dict1 = myia.fitcomponents(box=src_box, rms=img_rms, dooff=True, estimates=prefix1+'estimates.txt', logfile=prefix1+'logfile.txt')
                
                        found = True

            myia.close()

            if found == False: continue

            myia.open(img_sky_pbcor)
            if abs(src_dict1['zerooff']['value']/img_rms) < zerooff_snr:
                src_dict['component'+str(i)]['fitcomp'] = myia.fitcomponents(box=src_box, rms=img_rms, dooff=False, estimates=prefix1+'estimates.txt', logfile=prefix1+'logfile.txt')
            else:
                src_dict['component'+str(i)]['fitcomp'] = myia.fitcomponents(box=src_box, rms=img_rms, dooff=True, estimates=prefix1+'estimates.txt', logfile=prefix1+'logfile.txt')
            myia.close()

        for i in range(src_dict['nelements']):

            if 'fitcomp' not in src_dict['component'+str(i)].keys(): continue

            src_dict1 = src_dict['component'+str(i)]['fitcomp']

            if src_dict1['results']['nelements'] != 1: continue
            if src_dict1['converged'][0] != True: continue

            src_dict1 = src_dict1['results']['component0']

            peakX0 = src_dict['component'+str(i)]['pixelcoords'][0]
            peakY0 = src_dict['component'+str(i)]['pixelcoords'][1]
            peakX1 = src_dict1['pixelcoords'][0]
            peakY1 = src_dict1['pixelcoords'][1]
            peakDist = np.sqrt((peakX0-peakX1)**2 + (peakY0-peakY1)**2)

            if peakDist > 1: continue

            if 'zerooff' in src_dict['component'+str(i)]['fitcomp']:
                src_dict1['zerooff'] = src_dict['component'+str(i)]['fitcomp']['zerooff']

            src_dict1['pixelsperarcsec'] = src_dict['component'+str(i)]['fitcomp']['pixelsperarcsec']

            src_dict1['image filename'] = img_sky_pbcor
            src_dict1['shape']['direction']['RA'] = myqa.angle(src_dict1['shape']['direction']['m0'], form=['time'], prec=9)
            src_dict1['shape']['direction']['DEC'] = myqa.angle(src_dict1['shape']['direction']['m1'], prec=9)

            src_dict2[i] = src_dict1

        if src_dict2 != {}:
            for j in src_dict2.keys():
                src_dict2[j]['pixelcoords'] = src_dict2[j]['pixelcoords'].tolist()
                src_dict2[j]['pixelsperarcsec'] = src_dict2[j]['pixelsperarcsec'].tolist()
                src_dict2[j]['flux']['error'] = src_dict2[j]['flux']['error'].tolist()
                src_dict2[j]['flux']['value'] = src_dict2[j]['flux']['value'].tolist()
                if 'zerooff' in src_dict2[j].keys(): src_dict2[j]['zerooff']['value'] = src_dict2[j]['zerooff']['value'].tolist()

    os.system('rm -Rf '+img_sky_pbuncor)

    return(src_dict2)

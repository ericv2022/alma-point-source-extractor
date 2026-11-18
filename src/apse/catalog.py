"""Source filtering and catalog formatting from validated APSE v0.1.0.

Scientific algorithms intentionally unchanged.
"""
from shapely.geometry import Point
from shapely.affinity import scale, rotate

def create_ellipse(center, axes, inclination):

    p = Point(*center)
    c = p.buffer(1)
    ellipse = scale(c, *axes)
    ellipse = rotate(ellipse, inclination)

    return ellipse


def filterSources(src_dict, pointSourcesOnly=True, noBackgroundEmission=True, isolatedSourcesOnly=True):

    src_dict1 = {}

    for i in src_dict.keys():

        if pointSourcesOnly == True and src_dict[i]['ispoint'] != True: continue

        if noBackgroundEmission == True and 'zerooff' in src_dict[i].keys(): continue

        if isolatedSourcesOnly == True:

            peakX0 = src_dict[i]['pixelcoords'][0]
            peakY0 = src_dict[i]['pixelcoords'][1]
            bMaj = src_dict[i]['shape']['majoraxis']['value']
            bMin = src_dict[i]['shape']['minoraxis']['value']
            bPa = src_dict[i]['shape']['positionangle']['value']
            pixelsperarcsec = max(src_dict[i]['pixelsperarcsec'])

            ellipse0 = create_ellipse((peakX0, peakY0), (3*bMaj/pixelsperarcsec, 3*bMin/pixelsperarcsec), 90+bPa)

            found = False

            for j in src_dict.keys():

                if j == i: continue

                peakX0 = src_dict[j]['pixelcoords'][0]
                peakY0 = src_dict[j]['pixelcoords'][1]
                bMaj = src_dict[j]['shape']['majoraxis']['value']
                bMin = src_dict[j]['shape']['minoraxis']['value']
                bPa = src_dict[j]['shape']['positionangle']['value']
                pixelsperarcsec = max(src_dict[j]['pixelsperarcsec'])

                ellipse1 = create_ellipse((peakX0, peakY0), (3*bMaj/pixelsperarcsec, 3*bMin/pixelsperarcsec), 90+bPa)

                if ellipse1.intersects(ellipse0):
                    found = True
                    break

            if found == True: continue

        src_dict1[i] = src_dict[i]

    return(src_dict1)


def makeSourceList(src_dict, addKeywords=True):

#     keywds = ['BMAJ', 'BMIN', 'BPA', 'BUNIT', 'RADESYS', 'SPECSYS', \
#         'TELESCOP', 'DATE-OBS', 'TIMESYS', 'CASAVER', 'MEMBER', \
#         'PIPEVER', 'PROPCODE', 'SPECMODE', 'WEIGHT', 'DATE', 'ORIGIN', \
#         'ROBUST', 'IMGURL', 'CTRFREQ', 'BNDWID', 'FREQUNIT']

    src_dict1 = {}
    ij = 0

    for i in src_dict.keys():

        src_dict1[ij] = {}

        src_dict1[ij]['RA'] = src_dict[i]['shape']['direction']['RA'][0]
        src_dict1[ij]['DEC'] = src_dict[i]['shape']['direction']['DEC'][0]
        src_dict1[ij]['FLUX'] = src_dict[i]['flux']['value'][0]
        src_dict1[ij]['FLUXERR'] = src_dict[i]['flux']['error'][0]

#         if addKeywords == True:
# 
#             keyw_dict = extractMetadata(src_dict[i]['image filename'])
# 
#             for kk in keywds:
#                 if kk in keyw_dict.keys():
#                     src_dict1[ij][kk] = keyw_dict[kk]
#                 else:
#                     src_dict1[ij][kk] = ''

        ij += 1

    return(src_dict1)

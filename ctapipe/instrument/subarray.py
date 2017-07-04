"""
Description of Arrays or Subarrays of telescopes
"""

from collections import defaultdict

import numpy as np
from astropy import units as u
from astropy.table import Table


class SubarrayDescription:
    """
    Collects the `TelescopeDescription` of all telescopes along with their
    positions on the ground.

    Parameters
    ----------
    name: str
        name of this subarray
    tel_positions: dict(float)
        dict of telescope positions by tel_id
    tel_descriptions: dict(TelescopeDescription)
        array of TelescopeDescriptions by tel_id
    """

    def __init__(self, name, tel_positions=None, tel_descriptions=None):

        self.name = name
        self.positions = tel_positions or dict()
        self.tels = tel_descriptions or dict()

        assert set(self.positions.keys()) == set(self.tels.keys())

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}(name='{}', num_tels={})".format(
            self.__class__.__name__,
            self.name,
            self.num_tels)

    @property
    def tel(self):
        """ for backward compatibility"""
        return self.tels

    @property
    def num_tels(self):
        return len(self.tels)

    def info(self, printer=print):
        """
        print descriptive info about subarray
        """

        teltypes = defaultdict(list)

        for tel_id, desc in self.tels.items():
            teltypes[str(desc)].append(tel_id)

        printer("Subarray : {}".format(self.name))
        printer("Num Tels : {}".format(self.num_tels))
        printer("Footprint: {:.2f}".format(self.footprint))
        printer("")
        printer("                TYPE  Num IDmin  IDmax")
        printer("=====================================")
        for teltype, tels in teltypes.items():
            printer("{:>20s} {:4d} {:4d} ..{:4d}".format(teltype,
                                                         len(tels),
                                                         min(tels),
                                                         max(tels)))

    @property
    def pos_x(self):
        """ telescope x position as array """
        return np.array([p[0].to('m').value for p in self.positions.values()]) * u.m

    @property
    def pos_y(self):
        """ telescope y positions as an array"""
        return np.array([p[1].to('m').value for p in self.positions.values()]) * u.m

    @property
    def tel_id(self):
        """ telescope IDs as an array"""
        return np.array(self.tel.keys())

    @property
    def footprint(self):
        """area of smallest circle containing array on ground"""
        x = self.pos_x
        y = self.pos_y
        return (np.hypot(x, y).max() ** 2 * np.pi).to('km^2')

    def to_table(self):
        """ convert to `astropy.table.Table` """
        ids = [x for x in self.tels.keys()]
        descs = [str(x) for x in self.tels.values()]
        mirror_types = [x.optics.mirror_type for x in self.tels.values()]
        tel_types = [x.optics.tel_type for x in self.tels.values()]
        tel_subtypes = [x.optics.tel_subtype for x in self.tels.values()]
        cam_types = [x.camera.cam_id for x in self.tels.values()]

        tab = Table(dict(tel_id=np.array(ids, dtype=np.short),
                         tel_pos_x=self.pos_x,
                         tel_pos_y=self.pos_y,
                         tel_type=tel_types,
                         tel_subtype=tel_subtypes,
                         mirror_type=mirror_types,
                         camera_type=cam_types,
                         tel_description=descs))
        return tab

    def select_subarray(self, name, tel_ids):
        """
        return a new SubarrayDescription that is a sub-array of this one

        Parameters
        ----------
        name: str
            name of new sub-selection
        tel_ids: list(int)
            list of telescope IDs to include in the new subarray

        Returns
        -------
        SubarrayDescription
        """

        tel_positions = {tid: self.positions[tid] for tid in tel_ids}
        tel_descriptions = {tid: self.tel[tid] for tid in tel_ids}

        newsub = SubarrayDescription(name, tel_positions=tel_positions,
                                     tel_descriptions=tel_descriptions)
        return newsub

    def peek(self):
        """
        Draw a quick matplotlib plot of the array
        """
        from matplotlib import pyplot as plt
        from astropy.visualization import quantity_support

        types = {str(tel) for tel in self.tels.values()}
        tab = self.to_table()

        plt.figure(figsize=(8, 8))

        with quantity_support():
            for teltype in types:
                tels = tab[tab['tel_description'] == teltype]['tel_id']
                sub = self.select_subarray(teltype, tels)
                radius = np.array([np.sqrt(tel.optics.mirror_area / np.pi).value
                                   for tel in sub.tels.values()])

                plt.scatter(sub.pos_x, sub.pos_y, s=radius * 8, alpha=0.5,
                            label=teltype)

            plt.legend(loc='best')
            plt.title(self.name)
            plt.tight_layout()
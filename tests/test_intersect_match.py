# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""pytest for intersect_match.py"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from geomeppy.recipes import translate_coords
from geomeppy.view_geometry import view_polygons

from eppy.iddcurrent import iddcurrent
from geomeppy.eppy_patches import IDF
from geomeppy.intersect_match import get_adjacencies
from geomeppy.intersect_match import getidfsurfaces
from geomeppy.intersect_match import intersect
from geomeppy.intersect_match import intersect_idf_surfaces
from geomeppy.intersect_match import is_hole
from geomeppy.intersect_match import match_idf_surfaces
from geomeppy.intersect_match import unique
from geomeppy.polygons import Polygon3D
from geomeppy.utilities import almostequal
from six import StringIO


idf_txt = """
Version, 8.5;
Building, Building 1, , , , , , , ;
Zone, z1 Thermal Zone, 0.0, 0.0, 0.0, 0.0, , 1, , , , , , Yes;
Zone, z2 Thermal Zone, 0.0, 0.0, 0.0, 0.0, , 1, , , , , , Yes;
BuildingSurface:Detailed, z1_FLOOR, Floor, , z1 Thermal Zone, ground, , NoSun, NoWind, , , 1.0, 2.1, 0.0, 2.0, 2.0, 0.0, 2.0, 1.0, 0.0, 1.0, 1.1, 0.0;
BuildingSurface:Detailed, z1_ROOF, Roof, , z1 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 2.0, 1.0, 0.5, 2.0, 2.0, 0.5, 1.0, 2.1, 0.5, 1.0, 1.1, 0.5;
BuildingSurface:Detailed, z1_WALL_0001, WALL, , z1 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 1.0, 1.1, 0.5, 1.0, 1.1, 0.0, 1.0, 2.1, 0.0, 1.0, 2.1, 0.5;
BuildingSurface:Detailed, z1_WALL_0002, Wall, , z1 Thermal Zone, Outdoors, , SunExposed, WindExposed, , , 1.0, 2.1, 0.5, 1.0, 2.1, 0.0, 2.0, 2.0, 0.0, 2.0, 2.0, 0.5;
BuildingSurface:Detailed, z1_WALL_0003, WALL, , z1 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 2.0, 2.0, 0.5, 2.0, 2.0, 0.0, 2.0, 1.0, 0.0, 2.0, 1.0, 0.5;
BuildingSurface:Detailed, z1_WALL_0004, WALL, , z1 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 2.0, 1.0, 0.5, 2.0, 1.0, 0.0, 1.0, 1.1, 0.0, 1.0, 1.1, 0.5;
BuildingSurface:Detailed, z2_FLOOR, Floor, , z2 Thermal Zone, ground, , NoSun, NoWind, , , 1.5, 3.05, 0.0, 2.5, 2.95, 0.0, 2.5, 1.95, 0.0, 1.5, 2.05, 0.0;
BuildingSurface:Detailed, z2_ROOF, Roof, , z2 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 2.5, 1.95, 0.5, 2.5, 2.95, 0.5, 1.5, 3.05, 0.5, 1.5, 2.05, 0.5;
BuildingSurface:Detailed, z2_WALL_0001, WALL, , z2 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 1.5, 2.05, 0.5, 1.5, 2.05, 0.0, 1.5, 3.05, 0.0, 1.5, 3.05, 0.5;
BuildingSurface:Detailed, z2_WALL_0002, WALL, , z2 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 1.5, 3.05, 0.5, 1.5, 3.05, 0.0, 2.5, 2.95, 0.0, 2.5, 2.95, 0.5;
BuildingSurface:Detailed, z2_WALL_0003, WALL, , z2 Thermal Zone, outdoors, , SunExposed, WindExposed, , , 2.5, 2.95, 0.5, 2.5, 2.95, 0.0, 2.5, 1.95, 0.0, 2.5, 1.95, 0.5;
BuildingSurface:Detailed, z2_WALL_0004, Wall, , z2 Thermal Zone, Outdoors, , SunExposed, WindExposed, , , 2.5, 1.95, 0.5, 2.5, 1.95, 0.0, 1.5, 2.05, 0.0, 1.5, 2.05, 0.5;
"""

idf_txt_ring = """
Version, 8.5;
Building, Building 1, , , , , , , ;
Zone, Thermal Zone 1, 0.0, 0.0, 0.0, 0.0, , 1, , , , , , Yes;
Zone, Thermal Zone 2, 0.0, 0.0, 0.0, 0.0, , 1, , , , , , Yes;
BuildingSurface:Detailed, z1 Floor 0001, Floor, , Thermal Zone 2, Ground, , NoSun, NoWind, , , 0.0, 2.9, 0.0, 0.0, 0.0, 0.0, -2.14, 0.0, 0.0, -2.14, 2.9, 0.0;
BuildingSurface:Detailed, z1 Wall 0001, Wall, , Thermal Zone 2, Outdoors, , SunExposed, WindExposed, , , -2.14, 0.0, 1.5, -2.14, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.5;
BuildingSurface:Detailed, z1 Wall 0002, Wall, , Thermal Zone 2, Outdoors, , SunExposed, WindExposed, , , -2.14, 2.9, 1.5, -2.14, 2.9, 0.0, -2.14, 0.0, 0.0, -2.14, 0.0, 1.5;
BuildingSurface:Detailed, z1 Wall 0003, Wall, , Thermal Zone 2, Outdoors, , SunExposed, WindExposed, , , 0.0, 2.9, 1.5, 0.0, 2.9, 0.0, -2.14, 2.9, 0.0, -2.14, 2.9, 1.5;
BuildingSurface:Detailed, z1 Wall 0004, Wall, , Thermal Zone 2, Outdoors, , SunExposed, WindExposed, , , 0.0, 0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 2.9, 0.0, 0.0, 2.9, 1.5;
BuildingSurface:Detailed, z1 Roof 0001, Roof, , Thermal Zone 2, Outdoors, , SunExposed, WindExposed, , , 0.0, 0.0, 1.5, 0.0, 2.9, 1.5, -2.14, 2.9, 1.5, -2.14, 0.0, 1.5;

BuildingSurface:Detailed, z2 Floor 0001, Floor, , Thermal Zone 1, Ground, , NoSun, NoWind, , , -0.259, 2.46, 1.5, -0.259, 0.4, 1.5, -1.68, 0.4, 1.5, -1.68, 2.46, 1.5;
BuildingSurface:Detailed, z2 Wall 0001, Wall, , Thermal Zone 1, Outdoors, , SunExposed, WindExposed, , , -0.259, 2.46, 3.0, -0.259, 2.46, 1.5, -1.68, 2.46, 1.5, -1.68, 2.46, 3.0;
BuildingSurface:Detailed, z2 Wall 0002, Wall, , Thermal Zone 1, Outdoors, , SunExposed, WindExposed, , , -0.259, 0.4, 3.0, -0.259, 0.4, 1.5, -0.259, 2.46, 1.5, -0.259, 2.46, 3.0;
BuildingSurface:Detailed, z2 Wall 0003, Wall, , Thermal Zone 1, Outdoors, , SunExposed, WindExposed, , , -1.68, 0.4, 3.0, -1.68, 0.4, 1.5, -0.259, 0.4, 1.5, -0.259, 0.4, 3.0;
BuildingSurface:Detailed, z2 Wall 0004, Wall, , Thermal Zone 1, Outdoors, , SunExposed, WindExposed, , , -1.68, 2.46, 3.0, -1.68, 2.46, 1.5, -1.68, 0.4, 1.5, -1.68, 0.4, 3.0;
BuildingSurface:Detailed, z2 Roof 0001, Roof, , Thermal Zone 1, Outdoors, , SunExposed, WindExposed, , , -0.259, 0.4, 3.0, -0.259, 2.46, 3.0, -1.68, 2.46, 3.0, -1.68, 0.4, 3.0;
"""

class TestSetCoords():

    def setup(self):
        iddfhandle = StringIO(iddcurrent.iddtxt)
        if IDF.getiddname() == None:
            IDF.setiddname(iddfhandle)
        
        self.idf = IDF(StringIO(idf_txt))
            
    def test_set_coords(self):
        idf = self.idf
        ggr = idf.idfobjects['GLOBALGEOMETRYRULES']        
        wall = idf.idfobjects['BUILDINGSURFACE:DETAILED'][0]
        poly1 = Polygon3D([(0,1,0),(0,0,0),(1,0,0),(1,1,0)])
        wall.setcoords(poly1, ggr)

def test_unique():
    poly1 = Polygon3D([(0,1,0),(0,0,0),(1,0,0),(1,1,0)])
    poly2 = Polygon3D([(1,1,0),(1,0,0),(0,0,0),(0,1,0)])
    poly3 = Polygon3D([(0,1,0),(1,1,0),(1,0,0),(0,0,0)])
    assert poly1 != poly2
    assert poly2 == poly3
    polys = [poly1, poly2, poly3]
    unique_polys = unique(polys)
    assert len(unique_polys) == 2
    for poly in polys:
        assert poly in unique_polys
    
    
class TestSimpleTestPolygons():
    
    def test_simple_match(self):
        """
        The intersect function should just return the two polygons.
         ___  
        | 1 |
        |_2_| 

        """
        poly1 = Polygon3D([(0,1,0),(0,0,0),(1,0,0),(1,1,0)])
        poly2 = Polygon3D([(1,1,0),(1,0,0),(0,0,0),(0,1,0)])
        adjacencies = [(poly1, poly2)]
        result = intersect(*adjacencies[0])
        expected = [poly1, poly2]
        assert len(result) == len(expected)
        for poly in expected:
            assert poly in result
    
    def test_simple_overlap(self):
        """
        The intersect function should return four surfaces.
         __ ___ __ 
        | 1| 1 |  |  
        |__|_2_|_2| 

         __ ___ __ 
        | 1| 3 |  |  
        |__|_4_|_2| 

        """
        poly1 = Polygon3D([(0,1,0),(0,0,0),(2,0,0),(2,1,0)])
        poly2 = Polygon3D([(3,1,0),(3,0,0),(1,0,0),(1,1,0)])
        adjacencies = [(poly1, poly2)]
        poly1 = Polygon3D([(0,1,0),(0,0,0),(1,0,0),(1,1,0)])
        poly2 = Polygon3D([(3,1,0),(3,0,0),(2,0,0),(2,1,0)])
        poly3 = Polygon3D([(1,1,0),(1,0,0),(2,0,0),(2,1,0)])
        poly4 = Polygon3D([(2,1,0),(2,0,0),(1,0,0),(1,1,0)])
        result = intersect(*adjacencies[0])
        expected = [poly1, poly2, poly3, poly4]
        assert len(result) == len(expected)
        for poly in expected:
            assert poly in result

    def test_simple_hole(self):
        """
         _________ 
        | 1 ___   |  
        |  | 2 |  |
        |  |___|  | 
        |_________|
        
         ________ 
        |\ ___   |  
        |1| 2 | 4|
        | |_3_|  | 
        |/_______|
        
        """
        poly1 = Polygon3D([(0,4,0),(0,0,0),(4,0,0),(4,4,0)])
        poly2 = Polygon3D([(2,2,0),(2,1,0),(1,1,0),(1,2,0)])
        adjacencies = [(poly1, poly2)]
        
        poly1 = Polygon3D([(0,4,0), (0,0,0), (1,1,0), (1,2,0)])  # smaller section
        poly2 = Polygon3D([(1,2,0),(1,1,0),(2,1,0),(2,2,0)])  # inverse hole
        poly3 = Polygon3D([(2,2,0),(2,1,0),(1,1,0),(1,2,0)])  # hole
        poly4 = Polygon3D([(4,4,0), (0,4,0), (1,2,0), (2,2,0),
                           (2,1,0), (1,1,0), (0,0,0), (4,0,0)])  # larger section
        result = intersect(*adjacencies[0])
        expected = [poly1, poly2, poly3, poly4]
        assert len(result) == len(expected)
        for poly in expected:
            assert poly in result
                
    def test_three_overlapping(self):
        """
         __ ___ __ __
        | 1| 1 | 3| 3|  
        |__|_2_|_2|__| 

         __ ___ __ __
        | 1| 2 | 4| 6|  
        |__|_3_|_5|__| 
        
        """
        poly1 = Polygon3D([(0,1,0),(0,0,0),(2,0,0),(2,1,0)])
        poly2 = Polygon3D([(3,1,0),(3,0,0),(1,0,0),(1,1,0)])
        poly3 = Polygon3D([(2,1,0),(2,0,0),(4,0,0),(4,1,0)])
        adjacencies = [(poly1, poly2),
                       (poly2, poly3)]
        poly1 = Polygon3D([(0,1,0),(0,0,0),(1,0,0),(1,1,0)])
        poly2 = Polygon3D([(2,1,0),(2,0,0),(1,0,0),(1,1,0)])
        poly3 = Polygon3D([(1,1,0),(1,0,0),(2,0,0),(2,1,0)])
        poly4 = Polygon3D([(2,1,0),(2,0,0),(3,0,0),(3,1,0)])
        poly5 = Polygon3D([(3,1,0),(3,0,0),(2,0,0),(2,1,0)])
        poly6 = Polygon3D([(3,1,0),(3,0,0),(4,0,0),(4,1,0)])
        expected = [poly1, poly2, poly3, poly4, poly5, poly6]
        
        result = intersect(*adjacencies[0])
        result.extend(intersect(*adjacencies[1]))
        result = unique(result)

        assert len(result) == len(expected)
        for poly in expected:
            assert poly in result
    
    def test_double_overlap(self):
        """
         __________
        |__1_______| 
        | 1 | 2 |1 |
        |_2_|   |2_|
        |__________|
        
         __________
        |__1________| 
        | 2 | 4 | 5 |
        |_3_|   |_6_|
        |___________|
        
        """
        poly1 = Polygon3D([(0,2,0),(0,0,0),(3,0,0),(3,2,0)])
        poly2 = Polygon3D([(3,3,0),(3,1,0),(2,1,0),(2,2,0),
                           (1,2,0),(1,1,0),(0,1,0),(0,3,0)])
        adjacencies = [(poly1, poly2)]
        
        poly1 = Polygon3D([(3,3,0), (3,2,0), (0,2,0), (0,3,0)]) 
        poly2 = Polygon3D([(0,2,0), (0,1,0), (1,1,0), (1,2,0)])
        poly3 = Polygon3D([(1,2,0), (1,1,0), (0,1,0), (0,2,0)])
        poly4 = Polygon3D([(1,2,0), (1,1,0), (0,1,0), (0,0,0),
                           (3,0,0), (3,1,0), (2,1,0), (2,2,0)])
        poly5 = Polygon3D([(2,2,0), (2,1,0), (3,1,0), (3,2,0)])
        poly6 = Polygon3D([(3,2,0), (3,1,0), (2,1,0), (2,2,0)])

        result = intersect(*adjacencies[0])
        expected = [poly1, poly2, poly3, poly4, poly5, poly6]
        assert len(result) == len(expected)
        assert len(result) == len(expected)
        for poly in expected:
            assert poly in result
        
    def test_vertically_offset(self):
        """
         ___
        |_1_|
        | 1 |
        |_2_|
        |_2_|
         ___
        |_1_|
        | 2 |
        |_3_|
        |_4_|
         
        """
        poly1 = Polygon3D([(0,0,1),(0,0,0),(2,0,0),(2,0,1)])
        poly2 = Polygon3D([(3,0,1),(3,0,0),(1,0,0),(1,0,1)])
        adjacencies = [(poly1, poly2)]
        poly1 = Polygon3D([(0,0,1),(0,0,0),(1,0,0),(1,0,1)])
        poly2 = Polygon3D([(3,0,1),(3,0,0),(2,0,0),(2,0,1)])
        poly3 = Polygon3D([(1,0,1),(1,0,0),(2,0,0),(2,0,1)])
        poly4 = Polygon3D([(2,0,1),(2,0,0),(1,0,0),(1,0,1)])
        result = intersect(*adjacencies[0])
        expected = [poly1, poly2, poly3, poly4]
        assert len(result) == len(expected)
        for poly in expected:
            assert poly in result

        
class TestMatchSurfaces():

    def setup(self):
        iddfhandle = StringIO(iddcurrent.iddtxt)
        if IDF.getiddname() == None:
            IDF.setiddname(iddfhandle)
        
        self.idf = IDF(StringIO(idf_txt))
            
    def test_match_idf_surfaces(self):
        idf = self.idf
        intersect_idf_surfaces(idf)
        match_idf_surfaces(idf)
        idf.printidf()
        inside_wall = idf.getobject(
            'BUILDINGSURFACE:DETAILED', 'z1_WALL_0002_1')
        assert inside_wall.Outside_Boundary_Condition == 'surface'
        assert inside_wall.Outside_Boundary_Condition_Object == 'z2_WALL_0004_1'
        
        outside_wall = idf.getobject(
            'BUILDINGSURFACE:DETAILED', 'z1_WALL_0002_2')
        assert outside_wall.Outside_Boundary_Condition == 'outdoors'
        assert outside_wall.Outside_Boundary_Condition_Object == ''
        
        ground = idf.getobject(
            'BUILDINGSURFACE:DETAILED', 'z1_FLOOR')
        assert ground.Outside_Boundary_Condition == 'ground'
        assert ground.Outside_Boundary_Condition_Object == ''
        

class TestAdjacencies():
    
    def setup(self):
        iddfhandle = StringIO(iddcurrent.iddtxt)
        if IDF.getiddname() == None:
            IDF.setiddname(iddfhandle)
        
        self.idf = IDF(StringIO(idf_txt))
            
    def test_get_adjacencies(self):
        surfaces = getidfsurfaces(self.idf)
        adjacencies = get_adjacencies(surfaces)
        assert (u'BuildingSurface:Detailed', u'z1_WALL_0002') in adjacencies
        assert (u'BuildingSurface:Detailed', u'z2_WALL_0004') in adjacencies
        assert len(adjacencies) == 2
        
        
def test_intersect():
    poly1 = Polygon3D([(1.0, 2.1, 0.5), (1.0, 2.1, 0.0),
                       (2.0, 2.0, 0.0), (2.0, 2.0, 0.5)])
    poly2 = Polygon3D([(2.5, 1.95, 0.5), (2.5, 1.95, 0.0),
                       (1.5, 2.05, 0.0), (1.5, 2.05, 0.5)])
    intersection = poly1.intersect(poly2)[0]
#    view_polygons({'blue': [poly1, poly2], 'red': [intersect]})
    assert not is_hole(poly1, intersection)
    assert not is_hole(poly2, intersection)


def test_real_intersect():
    """
    Test that we can make a previously failing test pass by moving to the
    origin first.
    
    """
    poly1 = Polygon3D(
        [(526492.65, 185910.65, 6.0), (526492.65, 185910.65, 3.0),
         (526489.05, 185916.45, 3.0), (526489.05, 185916.45, 6.0)])
    poly2 = Polygon3D(
        [(526489.05, 185916.45, 5.0), (526489.05, 185916.45, 2.5),
        (526492.65, 185910.65, 2.5), (526492.65, 185910.65, 5.0)])
    min_x = min(min(s.xs) for s in [poly1, poly2])
    min_y = min(min(s.ys) for s in [poly1, poly2])
    poly1 = Polygon3D(translate_coords(poly1, [-min_x, -min_y, 0]))
    poly2 = Polygon3D(translate_coords(poly2, [-min_x, -min_y, 0]))
    intersection = Polygon3D(translate_coords(
        poly1.intersect(poly2)[0], [min_x, min_y, 0]))
    poly1 = Polygon3D(translate_coords(poly1, [min_x, min_y, 0]))
    poly2 = Polygon3D(translate_coords(poly2, [min_x, min_y, 0]))
#    view_polygons({'blue': [poly1, poly2]})#, 'red': [intersection]})
    assert not is_hole(poly1, intersection)
    assert not is_hole(poly2, intersection)


def test_is_hole():
    """Test if a surface represents a hole in one of the surfaces.
    """
    # opposite faces (all touching edges)
    poly1 = Polygon3D([(0,4,0),(0,0,0),(4,0,0),(4,4,0)])
    poly2 = Polygon3D(reversed([(0,4,0),(0,0,0),(4,0,0),(4,4,0)]))
    intersection = poly1.intersect(poly2)[0]
    assert not is_hole(poly1, intersection)
    assert not is_hole(poly2, intersection)

    # poly2 is within poly1 and reversed (no touching edges)
    poly1 = Polygon3D([(0,4,0),(0,0,0),(4,0,0),(4,4,0)])
    poly2 = Polygon3D(reversed([(1,3,0),(1,1,0),(3,1,0),(3,3,0)]))
    intersection = poly1.intersect(poly2)[0]
    assert is_hole(poly1, intersection)
    assert not is_hole(poly2, intersection)

    # poly2 is within poly1 and reversed (touches at x=0)
    poly1 = Polygon3D([(0,4,0),(0,0,0),(4,0,0),(4,4,0)])
    poly2 = Polygon3D(reversed([(0,3,0),(0,1,0),(3,1,0),(3,3,0)]))
    intersection = poly1.intersect(poly2)[0]
    assert not is_hole(poly1, intersection)
    assert not is_hole(poly2, intersection)

    # poly2 overlaps poly1
    poly1 = Polygon3D([(1,4,0),(1,0,0),(5,0,0),(5,4,0)])
    poly2 = Polygon3D(reversed([(0,3,0),(0,1,0),(3,1,0),(3,3,0)]))
    intersection = poly1.intersect(poly2)[0]
    assert not is_hole(poly1, intersection)
    assert not is_hole(poly2, intersection)


class TestIntersectMatchRing():
    
    def setup(self):
        iddfhandle = StringIO(iddcurrent.iddtxt)
        if IDF.getiddname() == None:
            IDF.setiddname(iddfhandle)
        
        self.idf = IDF(StringIO(idf_txt_ring))
        
    def test_intersect_idf_surfaces(self):       
        idf = self.idf        
        starting = len(idf.idfobjects['BUILDINGSURFACE:DETAILED'])
        intersect_idf_surfaces(idf)
        idf.set_default_constructions()
        ending = len(idf.idfobjects['BUILDINGSURFACE:DETAILED'])
        assert starting == 12
        assert ending == 14
        for name in ['z1 Roof 0001_1',
                     'z1 Roof 0001_2',
                     'z1 Roof 0001_3',
                     'z2 Floor 0001_1']:
            obj = idf.getobject('BUILDINGSURFACE:DETAILED', name)
            assert obj


class TestIntersectMatch():
    
    def setup(self):
        iddfhandle = StringIO(iddcurrent.iddtxt)
        if IDF.getiddname() == None:
            IDF.setiddname(iddfhandle)
        
        self.idf = IDF(StringIO(idf_txt))
            
    def test_getidfsurfaces(self):    
        idf = self.idf
        surfaces = getidfsurfaces(idf)
        assert len(surfaces) == 12
    
    def test_intersect_idf_surfaces(self):       
        idf = self.idf        
        starting = len(idf.idfobjects['BUILDINGSURFACE:DETAILED'])
        intersect_idf_surfaces(idf)
        ending = len(idf.idfobjects['BUILDINGSURFACE:DETAILED'])
        assert starting == 12
        assert ending == 14
        
        for name in ['z1_WALL_0002_1',
                     'z1_WALL_0002_2',
                     'z2_WALL_0004_1',
                     'z2_WALL_0004_2']:
            obj = idf.getobject('BUILDINGSURFACE:DETAILED', name)
            assert obj

def test_real_scale():
    """Test building, intersecting and matching from a real building footprint.
    """
    iddfhandle = StringIO(iddcurrent.iddtxt)
    if IDF.getiddname() == None:
        IDF.setiddname(iddfhandle)
    
    idf = IDF(StringIO('Version, 8.5;'))
    poly1 = [(526492.65,185910.65),(526489.05,185916.45),
             (526479.15,185910.3),(526482.65,185904.6),
             (526492.65,185910.65)]
    poly2 = [(526483.3,185903.15),(526483.5,185903.25),
             (526482.65,185904.6),(526479.15,185910.3),
             (526489.05,185916.45),(526492.65,185910.65),
             (526493.4,185909.4),(526500,185913.95),
             (526500.45,185914.3),(526500,185914.85),
             (526497.4,185918.95),(526499.45,185920.2),
             (526494.4,185928.35),(526466.05,185910.95),
             (526471.1,185902.75),(526473.05,185903.9),
             (526476.2,185898.8),(526479.95,185901.1),
             (526483.3,185903.15)]
    idf.add_block('small', poly1, 6.0, 2)
    idf.add_block('large', poly2, 5.0, 2)
    idf.translate_to_origin()
    idf.intersect_match()
    idf.set_wwr(0.25)
    walls = idf.getsurfaces('wall')
    # look for a wall which should have been split
    assert 'Block large Storey 1 Wall 0003' not in [w.Name for w in walls]
    # look for another wall which should have been split
    assert 'Block large Storey 1 Wall 0005' not in [w.Name for w in walls]
    # look for a wall which should be an internal wall
    wall = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block small Storey 1 Wall 0002_1')
    assert wall.Outside_Boundary_Condition != 'outdoors'
    # look for another wall which should be an internal wall
    wall = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block large Storey 1 Wall 0003_2')
    assert wall.Outside_Boundary_Condition != 'outdoors'
    
    # look for two walls which are being incorrectly duplicated
    wall_1 = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block small Storey 0 Wall 0001_1')
    wall_2 = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block small Storey 0 Wall 0001_4')
    
    if wall_1 and wall_2:
        assert not almostequal(wall_1.coords, wall_2.coords)
    
    # look for two walls which are being incorrectly duplicated
    wall_1 = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block large Storey 1 Wall 0005_3')
    wall_2 = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block large Storey 1 Wall 0005_2')
    
    if wall_1 and wall_2:
        assert not almostequal(wall_1.coords, wall_2.coords)
    
    # look for two walls which are being incorrectly duplicated
    wall_1 = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block large Storey 1 Wall 0004_3')
    wall_2 = idf.getobject(
        'BUILDINGSURFACE:DETAILED', 'Block large Storey 1 Wall 0004_1')
    
    if wall_1 and wall_2:
        assert not almostequal(wall_1.coords, wall_2.coords)

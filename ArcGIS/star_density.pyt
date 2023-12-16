# -*- coding: utf-8 -*-
# Tool written by Greta Freitag for GISG 111 at San Diego Mesa College

import arcpy
import shapely.geometry
import random
from arcgis.geometry import BaseGeometry

@classmethod
def from_shapely(cls, shapely_geometry):
    return cls(shapely_geometry.__geo_interface__)

BaseGeometry.from_shapely = from_shapely

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Star Lattice"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        inFeatures = arcpy.Parameter(
            displayName="Input Features",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        inFeatures.filter.list = ["Polygon"]

        outName = arcpy.Parameter(
            displayName="Output Feature Class Name",
            name="out_feature_class",
            datatype="GPString",
            parameterType="Required",
            direction="Input")


        inField = arcpy.Parameter(
            displayName="Input Field",
            name="input_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        inField.parameterDependencies = [inFeatures.name]

        minStars = arcpy.Parameter(
            displayName="Minimum Stars",
            name="min_stars",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
        )

        minStars.value = 1.0

        maxStars = arcpy.Parameter(
            displayName="Maximum Stars",
            name="max_stars",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
        )

        maxStars.value = 2.0

        in_workspace = arcpy.Parameter(
            displayName="Input Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )


        params = [inFeatures, in_workspace, outName, inField, minStars, maxStars]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_features = parameters[0].valueAsText
        in_workspace = parameters[1].valueAsText
        out_fc = parameters[2].valueAsText
        in_field = parameters[3].valueAsText
        min_count = float(parameters[4].valueAsText)
        max_count = float(parameters[5].valueAsText)

        # Creating a stars feature class
        fc_list = []
        spatial_ref = arcpy.Describe(in_features).spatialReference
        newFeature = arcpy.CreateFeatureclass_management(in_workspace, out_fc, "POINT", spatial_reference=spatial_ref)
        arcpy.AddField_management(arcpy.Describe(out_fc).catalogPath,'X_Coord','DOUBLE')
        arcpy.AddField_management(arcpy.Describe(out_fc).catalogPath,'Y_Coord','DOUBLE')

        # finding the minimum and maximum input field values
        minNum = float("inf")
        maxNum = 0.0
        minArea = float("inf")
        maxArea = 0.0
        with arcpy.da.SearchCursor(in_features, ["SHAPE@AREA", in_field]) as cursor:
            for row in cursor:
                area = row[0]
                val = row[1]
                if val is not None:
                    if val<minNum:
                        minNum = val
                    if val>maxNum:
                        maxNum = val
                if area is not None:
                    if area<minArea:
                        minArea = area
                    if area>maxArea:
                        maxArea = area

        with arcpy.da.SearchCursor(in_features, ["SHAPE@", "SHAPE@AREA", in_field]) as cursor:
            # Iterating through state polygons
            for row in cursor:
                polygon = row[0]
                area = row[1]
                value = row[2]

                # Polygon extents for generating points
                left_ex = polygon.extent.XMin
                top_ex = polygon.extent.YMax
                bottom_ex = polygon.extent.YMin
                right_ex = polygon.extent.XMax

                # Defining a shapely polygon
                coor = []
                for part in polygon:
                    for pt in part:
                        if pt:
                            coor.append((pt.X, pt.Y))
                        else:
                            arcpy.AddMessage(part)
                shapely_polygon = shapely.Polygon(coor)

                if value is None:  # Error catch
                    starCount = 0
                else:
                    # Transforming the range of values to the user-provided range of number of stars
                    starCount = max_count - ((((value - minNum) * (max_count - min_count)) / (maxNum - minNum)) + min_count) + min_count
                    arcpy.AddMessage(starCount)
                    # Changing the area to a normalizing factor
                    # Potential error case: all areas the same size
                    areaNorm = (((area - minArea)*0.95) / (maxArea - minArea)) + 0.05
                    # Normalizing number of stars by area
                    starNorm = int(starCount*areaNorm)
                for i in range(0, starNorm):
                    # Generating all the points.
                    with arcpy.da.InsertCursor(arcpy.Describe(out_fc).catalogPath, ['SHAPE@XY','X_Coord','Y_Coord']) as cursor:
                        x, y = self.getPoint(left_ex,right_ex,top_ex,bottom_ex,shapely_polygon)
                        cursor.insertRow(((x,y),x,y))
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

    def getPoint(self, left_ex, right_ex, top_ex, bottom_ex, polygon):
        x = random.uniform(left_ex, right_ex)
        y = random.uniform(bottom_ex, top_ex)
        genPoint = shapely.Point(x,y)
        while not polygon.contains(genPoint):
            x = random.uniform(left_ex, right_ex)
            y = random.uniform(bottom_ex, top_ex)
            genPoint = shapely.Point(x,y)
        return x, y
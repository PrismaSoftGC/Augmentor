"""
The Operations module contains classes for all operations used by Augmentor. 

The classes contained in this module are not called or instantiated directly
by the user, instead the user interacts with the 
:class:`~Augmentor.Pipeline.Pipeline` class and uses the utility functions contained 
there. 
 
In this module, each operation is a subclass of type :class:`Operation`.
The :class:`~Augmentor.Pipeline.Pipeline` objects expect :class:`Operation` 
types, and therefore all operations are of type :class:`Operation`, and 
provide their own implementation of the :func:`~Operation.perform_operation`
function.
 
Hence, the documentation for this module is intended for developers who 
wish to extend Augmentor or wish to see how operations function internally.

For detailed information on extending Augmentor, see :ref:`extendingaugmentor`.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from PIL import Image, ImageOps
from .ImageUtilities import extract_paths_and_extensions
import math
from math import floor, ceil

import numpy as np
# from skimage import img_as_ubyte
# from skimage import transform

import os
import random
import warnings

# Python 2-3 compatibility - not currently needed.
# try:
#    from StringIO import StringIO
# except ImportError:
#    from io import StringIO


class Operation(object):
    """
    The class :class:`Operation` represents the base class for all operations
    that can be performed. Inherit from :class:`Operation`, overload 
    its methods, and instantiate super to create a new operation. See 
    the section on extending Augmentor with custom operations at 
    :ref:`extendingaugmentor`.
    """
    def __init__(self, probability):
        """
        All operations must at least have a :attr:`probability` which is 
        initialised when creating the operation's object.
        
        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline. 
        :type probability: Float
        """
        self.probability = probability

    def __str__(self):
        """
        Used to display a string representation of the operation, which is 
        used by the :func:`Pipeline.status` to display the current pipeline's
        operations in a human readable way.
        
        :return: A string representation of the operation. Can be overridden 
         if required, for example as is done in the :class:`Rotate` class. 
        """
        return self.__class__.__name__

    def perform_operation(self, image):
        """
        Perform the operation on the image. Each operation must at least 
        have this function, which accepts an image of type PIL.Image, performs
        its operation, and returns an image of type PIL.Image.
        
        :param image: The image to transform.
        :type image: PIL.Image
        :return: The transformed image of type PIL.Image.
        """
        raise RuntimeError("Illegal call to base class.")

    @staticmethod
    def extract_paths_and_extensions(image_path):
        """
        Utility function to extract the file name, extension and root path 
        of an image's full path. 
        
        :param image_path: The path of the image.
        :return: A 3-tuple containing the file name, extension, and root path.
        """
        file_name, extension = os.path.splitext(image_path)
        root_path = os.path.dirname(image_path)

        return file_name, extension, root_path


class HistogramEqualisation(Operation):
    """
    The class :class:`HistogramEqualisation` is used to perform histogram
    equalisation on images passed to its :func:`perform_operation` function.
    """
    def __init__(self, probability):
        """
        As there are no further user definable parameters, the class is 
        instantiated using only the :attr:`probability` argument.
        
        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline.
        :type probability: Float
        """
        Operation.__init__(self, probability)

    def perform_operation(self, image):
        """
        Performs histogram equalisation on the image passed as an argument 
        and returns the equalised image. There are no user definable parameters
        for this method.
        
        :param image: The image on which to perform the histogram equalisation.
        :type image: PIL.Image
        :return: The transformed image of type PIL.Image
        """
        # TODO: We may need to apply this to each channel:
        # If an image is a colour image, the histogram will
        # will be computed on the flattened image, which fires
        # a warning.
        # We may want to apply this instead to each colour channel,
        # but I see no reason why right now. It would remove
        # the need to catch these warnings, however.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ImageOps.equalize(image)


class Greyscale(Operation):
    """
    This class is used to convert images into greyscale. That is, it converts
    images into having only shades of grey (pixel value intensities) 
    varying from 0 to 255 which represent black and white respectively.
    
    .. seealso:: The :class:`BlackAndWhite` class.
    """
    def __init__(self, probability):
        """
        As there are no further user definable parameters, the class is 
        instantiated using only the :attr:`probability` argument.
        
        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline.
        :type probability: Float
        """
        Operation.__init__(self, probability)

    def perform_operation(self, image):
        """
        Converts the passed image to greyscale and returns the transformed 
        image. There are no user definable parameters for this method.
        
        :param image: The image to convert to greyscale.
        :type image: PIL.Image
        :return: The transformed image as type PIL.Image
        """
        return ImageOps.grayscale(image)


class Invert(Operation):
    """
    This class is used to negate images. That is to reverse the pixel values
    for any image processed by it.
    """
    def __init__(self, probability):
        """
        As there are no further user definable parameters, the class is 
        instantiated using only the :attr:`probability` argument.
        
        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline.
        :type probability: Float
        """
        Operation.__init__(self, probability)

    def perform_operation(self, image):
        """
        Negates the image passed as an argument. There are no user definable 
        parameters for this method.
        
        :param image: The image to negate.
        :type image: PIL.Image
        :return: The transformed image as type PIL.Image
        """
        return ImageOps.invert(image)


class BlackAndWhite(Operation):
    """
    This class is used to convert images into black and white. In other words,
    into using a 1-bit, monochrome binary colour palette. This is not to be 
    confused with greyscale, where an 8-bit greyscale pixel intensity range
    is used.
    
    .. seealso:: The :class:`Greyscale` class.
    """
    def __init__(self, probability, threshold):
        """
        As well as the required :attr:`probability` parameter, a 
        :attr:`threshold` can also be defined to define the cutoff point where
        a pixel is converted to black or white. The :attr:`threshold` defaults
        to 128 at the user-facing 
        :func:`~Augmentor.Pipeline.Pipeline.black_and_white` function. 
        
        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline.
        :param threshold: A value between 0 and 255 that defines the cut off
         point where an individual pixel is converted into black or white. 
        :type probability: Float
        :type threshold: Integer
        """
        Operation.__init__(self, probability)
        self.threshold = threshold

    def perform_operation(self, image):
        """
        Convert the image passed as an argument to black and white, 1-bit 
        monochrome. Uses the :attr:`threshold` passed to the constructor
        to control the cut-off point where a pixel is converted to black or 
        white.
        
        :param image: The image to convert into monochrome.
        :type image: PIL.Image
        :return: The converted image as type PIL.Image
        """
        image = ImageOps.grayscale(image)
        # See the Stack Overflow question:
        # http://stackoverflow.com/questions/18777873/convert-rgb-to-black-or-white
        # An alternative would be to use PIL.ImageOps.posterize(image=image, bits=1)
        return image.point(lambda x: 0 if x < self.threshold else 255, '1')


class Skew(Operation):
    """
    This class is used to perform perspective skewing on images. It allows
    for skewing from a total of 12 different perspectives.  
    """
    def __init__(self, probability, skew_type, magnitude):
        """
        As well as the required :attr:`probability` parameter, the type of
        skew that is performed is controlled using a :attr:`skew_type` and a 
        :attr:`magnitude` parameter. The :attr:`skew_type` controls the
        direction of the skew, while :attr:`magnitude` controls the degree
        to which the skew is performed.
        
        To see examples of the various skews, see :ref:`perspectiveskewing`.
        
        Images are skewed **in place** and an image of the same size is
        returned by this function. That is to say, that after a skew
        has been performed, the largest possible area of the same aspect ratio
        of the original image is cropped from the skewed image, and this is 
        then resized to match the original image size. The 
        :ref:`perspectiveskewing` section describes this in detail.
        
        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline. 
        :param skew_type: Must be one of ``TILT``, ``TILT_TOP_BOTTOM``, 
         ``TILT_LEFT_RIGHT``, or ``CORNER``.
         
         - ``TILT`` will randomly skew either left, right, up, or down.
           Left or right means it skews on the x-axis while up and down
           means that it skews on the y-axis.
         - ``TILT_TOP_BOTTOM`` will randomly skew up or down, or in other
           words skew along the y-axis.
         - ``TILT_LEFT_RIGHT`` will randomly skew left or right, or in other
           words skew along the x-axis.
         - ``CORNER`` will randomly skew one **corner** of the image either 
           along the x-axis or y-axis. This means in one of 8 different
           directions, randomly.
         
         To see examples of the various skews, see :ref:`perspectiveskewing`.  
                  
        :param magnitude: The degree to which the image is skewed.
        :type probability: Float
        :type skew_type: String
        :type magnitude: Integer
        """
        Operation.__init__(self, probability)
        self.skew_type = skew_type
        self.magnitude = magnitude

    def perform_operation(self, image):
        """
        Perform the skew on the passed image and returns the transformed 
        image. Uses the :attr:`skew_type` and :attr:`magnitude` parameters to 
        control the type of skew to perform as well as the degree to which it
        is performed.
        
        :param image: The image to skew.
        :type image: PIL.Image
        :return: The skewed image as type PIL.Image
        """

        w, h = image.size

        x1 = 0
        x2 = h
        y1 = 0
        y2 = w

        original_plane = [(y1, x1), (y2, x1), (y2, x2), (y1, x2)]

        max_skew_amount = max(w, h)

        if not self.magnitude:
            skew_amount = random.randint(1, max_skew_amount)
        elif self.magnitude:
            max_skew_amount /= self.magnitude
            skew_amount = max_skew_amount

        # We have two choices now: we tilt in one of four directions
        # or we skew a corner.

        if self.skew_type == "TILT" or self.skew_type == "TILT_LEFT_RIGHT" or self.skew_type == "TILT_TOP_BOTTOM":

            if self.skew_type == "TILT":
                skew_direction = random.randint(0, 3)
            elif self.skew_type == "TILT_LEFT_RIGHT":
                skew_direction = random.randint(0, 1)
            elif self.skew_type == "TILT_TOP_BOTTOM":
                skew_direction = random.randint(2, 3)

            if skew_direction == 0:
                # Left Tilt
                new_plane = [(y1, x1 - skew_amount),  # Top Left
                             (y2, x1),                # Top Right
                             (y2, x2),                # Bottom Right
                             (y1, x2 + skew_amount)]  # Bottom Left
            elif skew_direction == 1:
                # Right Tilt
                new_plane = [(y1, x1),                # Top Left
                             (y2, x1 - skew_amount),  # Top Right
                             (y2, x2 + skew_amount),  # Bottom Right
                             (y1, x2)]                # Bottom Left
            elif skew_direction == 2:
                # Forward Tilt
                new_plane = [(y1 - skew_amount, x1),  # Top Left
                             (y2 + skew_amount, x1),  # Top Right
                             (y2, x2),                # Bottom Right
                             (y1, x2)]                # Bottom Left
            elif skew_direction == 3:
                # Backward Tilt
                new_plane = [(y1, x1),                # Top Left
                             (y2, x1),                # Top Right
                             (y2 + skew_amount, x2),  # Bottom Right
                             (y1 - skew_amount, x2)]  # Bottom Left

        if self.skew_type == "CORNER":

            skew_direction = random.randint(0, 7)

            if skew_direction == 0:
                # Skew possibility 0
                new_plane = [(y1 - skew_amount, x1), (y2, x1), (y2, x2), (y1, x2)]
            elif skew_direction == 1:
                # Skew possibility 1
                new_plane = [(y1, x1 - skew_amount), (y2, x1), (y2, x2), (y1, x2)]
            elif skew_direction == 2:
                # Skew possibility 2
                new_plane = [(y1, x1), (y2 + skew_amount, x1), (y2, x2), (y1, x2)]
            elif skew_direction == 3:
                # Skew possibility 3
                new_plane = [(y1, x1), (y2, x1 - skew_amount), (y2, x2), (y1, x2)]
            elif skew_direction == 4:
                # Skew possibility 4
                new_plane = [(y1, x1), (y2, x1), (y2 + skew_amount, x2), (y1, x2)]
            elif skew_direction == 5:
                # Skew possibility 5
                new_plane = [(y1, x1), (y2, x1), (y2, x2 + skew_amount), (y1, x2)]
            elif skew_direction == 6:
                # Skew possibility 6
                new_plane = [(y1, x1), (y2, x1), (y2, x2), (y1 - skew_amount, x2)]
            elif skew_direction == 7:
                # Skew possibility 7
                new_plane = [(y1, x1), (y2, x1), (y2, x2), (y1, x2 + skew_amount)]

        if self.skew_type == "ALL":
            # Not currently in use, as it makes little sense to skew by the same amount
            # in every direction if we have set magnitude manually.
            # It may make sense to keep this, if we ensure the skew_amount below is randomised
            # and cannot be manually set by the user.
            corners = dict()
            corners["top_left"] = (y1 - random.randint(1, skew_amount), x1 - random.randint(1, skew_amount))
            corners["top_right"] = (y2 + random.randint(1, skew_amount), x1 - random.randint(1, skew_amount))
            corners["bottom_right"] = (y2 + random.randint(1, skew_amount), x2 + random.randint(1, skew_amount))
            corners["bottom_left"] = (y1 - random.randint(1, skew_amount), x2 + random.randint(1, skew_amount))

            new_plane = [corners["top_left"], corners["top_right"], corners["bottom_right"], corners["bottom_left"]]

        # To calculate the coefficients required by PIL for the perspective skew,
        # see the following Stack Overflow discussion: https://goo.gl/sSgJdj
        matrix = []

        for p1, p2 in zip(new_plane, original_plane):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

        A = np.matrix(matrix, dtype=np.float)
        B = np.array(original_plane).reshape(8)

        perspective_skew_coefficients_matrix = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        perspective_skew_coefficients_matrix = np.array(perspective_skew_coefficients_matrix).reshape(8)

        return image.transform(image.size,
                               Image.PERSPECTIVE,
                               perspective_skew_coefficients_matrix,
                               resample=Image.BICUBIC)


class Rotate(Operation):
    """
    This class is used to perform rotations on images by arbitrary numbers of
    degrees.
      
    Images are rotated **in place** and an image of the same size is
    returned by this function. That is to say, that after a rotation
    has been performed, the largest possible area of the same aspect ratio
    of the original image is cropped from the skewed image, and this is 
    then resized to match the original image size. The 
    :ref:`rotating` section describes this in detail and has example 
    images to demonstrate this.
    """
    def __init__(self, probability, rotation):
        """
        As well as the required :attr:`probability` parameter, the 
        :attr:`rotation` parameter controls the maximum number of degrees
        by which to rotate. 
        
        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline. 
        :param rotation: The maximum number of degrees to rotate by. 
        """
        Operation.__init__(self, probability)
        self.rotation = rotation

    def __str__(self):
        return "Rotate " + str(self.rotation)

    def perform_operation(self, image):
        """
        Rotate an image by an arbitrary number of degrees. The 
        `attr`:rotation` parameter controls the number of degrees by which the
        passed image is rotated.
        
        For developers who are looking at the function's source code, 
        the source can be better understood by taking into account the 
        following equations that were used to calculate the maximum area
        to crop from the rotated image:
        
        :math:`E = \\frac{\\frac{\\sin{\\theta_{a}}}{\\sin{\\theta_{b}}}\\Big(X-\\frac{\\sin{\\theta_{a}}}{\\sin{\\theta_{b}}} Y\\Big)}{1-\\frac{(\\sin{\\theta_{a}})^2}{(\\sin{\\theta_{b}})^2}}`

        which describes how :math:`E` is derived, and then follows 
        :math:`B = Y - E` and 
        :math:`A = \\frac{\\sin{\\theta_{a}}}{\\sin{\\theta_{b}}} B`.
        
        :param image: The image to rotate.
        :return: The rotated image.
        """
        if self.rotation == -1:
            random_factor = random.randint(1, 3)
            # TODO: Check if for a modulo 90 a resample is needed
            return image.rotate(90 * random_factor, expand=True, resample=Image.BICUBIC)
        else:
            # Get size before we rotate
            x = image.size[0]
            y = image.size[1]

            # Rotate, while expanding the canvas size
            image = image.rotate(self.rotation, expand=True, resample=Image.BICUBIC)

            # Get size after rotation, which includes the empty space
            X = image.size[0]
            Y = image.size[1]

            # Get our two angles needed for the calculation of the largest area
            angle_a = abs(self.rotation)
            angle_b = 90 - angle_a

            # We need the sin of angle a and b a few times
            sin_angle_a = math.sin(math.radians(angle_a))
            sin_angle_b = math.sin(math.radians(angle_b))

            # Now we find the maximum area of the rectangle that could be cropped
            E = (sin_angle_a / sin_angle_b) * \
                (Y - X * (sin_angle_a / sin_angle_b))
            E = E / 1 - (sin_angle_a ** 2 / sin_angle_b ** 2)
            B = X - E
            A = (sin_angle_a / sin_angle_b) * B

            # Crop this area from the rotated image
            image = image.crop((int(round(E)), int(round(A)), int(round(X - E)), int(round(Y - A))))

            # Return the image, re-sized to the size of the image passed originally
            return image.resize((x, y), resample=Image.BICUBIC)


class RotateRange(Operation):
    """
    This class is used to perform rotations on images by arbitrary numbers of
    degrees.

    Images are rotated **in place** and an image of the same size is
    returned by this function. That is to say, that after a rotation
    has been performed, the largest possible area of the same aspect ratio
    of the original image is cropped from the skewed image, and this is 
    then resized to match the original image size. The 
    :ref:`rotating` section describes this in detail and has example 
    images to demonstrate this.
    """
    def __init__(self, probability, max_left_rotation, max_right_rotation):
        """
        As well as the required :attr:`probability` parameter, the 
        :attr:`max_left_rotation` parameter controls the maximum number of 
        degrees by which to rotate to the left, while the 
        :attr:`max_right_rotation` controls the maximum number of degrees to
        rotate to the right. 

        :param probability: Controls the probability that the operation is 
         performed when it is invoked in the pipeline. 
        :param max_left_rotation: The maximum number of degrees to rotate 
         the image anti-clockwise.
        :param max_right_rotation: The maximum number of degrees to rotate
         the image clockwise.
        """
        Operation.__init__(self, probability)
        self.max_left_rotation = -abs(max_left_rotation)   # Ensure always negative
        self.max_right_rotation = abs(max_right_rotation)  # Ensure always positive

    def perform_operation(self, image):
        random_left = random.randint(self.max_left_rotation, -5)
        random_right = random.randint(5, self.max_right_rotation)

        left_or_right = random.randint(0, 1)

        rotation = 0

        if left_or_right == 0:
            rotation = random_left
        elif left_or_right == 1:
            rotation = random_right

        # Get size before we rotate
        x = image.size[0]
        y = image.size[1]

        # Rotate, while expanding the canvas size
        image = image.rotate(rotation, expand=True, resample=Image.BICUBIC)

        # Get size after rotation, which includes the empty space
        X = image.size[0]
        Y = image.size[1]

        # Get our two angles needed for the calculation of the largest area
        angle_a = abs(rotation)
        angle_b = 90 - angle_a

        # Python deals in radians so get our radians
        angle_a_rad = math.radians(angle_a)
        angle_b_rad = math.radians(angle_b)

        # Calculate the sins
        angle_a_sin = math.sin(angle_a_rad)
        angle_b_sin = math.sin(angle_b_rad)

        # Find the maximum area of the rectangle that could be cropped
        E = (math.sin(angle_a_rad)) / (math.sin(angle_b_rad)) * \
            (Y - X * (math.sin(angle_a_rad) / math.sin(angle_b_rad)))
        E = E / 1 - (math.sin(angle_a_rad) ** 2 / math.sin(angle_b_rad) ** 2)
        B = X - E
        A = (math.sin(angle_a_rad) / math.sin(angle_b_rad)) * B

        # Crop this area from the rotated image
        # image = image.crop((E, A, X - E, Y - A))
        image = image.crop((int(round(E)), int(round(A)), int(round(X - E)), int(round(Y - A))))

        # Return the image, re-sized to the size of the image passed originally
        return image.resize((x, y), resample=Image.BICUBIC)


class Resize(Operation):
    def __init__(self, probability, width, height, resample_filter):
        Operation.__init__(self, probability)
        self.width = width
        self.height = height
        self.resample_filter = resample_filter

    def perform_operation(self, image):
        # TODO: Automatically change this to ANTIALIAS or BICUBIC depending on the size of the file
        return image.resize((self.width, self.height), eval("Image.%s" % self.resample_filter))


class Flip(Operation):
    def __init__(self, probability, top_bottom_left_right):
        Operation.__init__(self, probability)
        self.top_bottom_left_right = top_bottom_left_right

    def perform_operation(self, image):
        if self.top_bottom_left_right == "LEFT_RIGHT":
            return image.transpose(Image.FLIP_LEFT_RIGHT)
        elif self.top_bottom_left_right == "TOP_BOTTOM":
            return image.transpose(Image.FLIP_TOP_BOTTOM)
        elif self.top_bottom_left_right == "RANDOM":
            random_axis = random.randint(0, 1)
            if random_axis == 0:
                return image.transpose(Image.FLIP_LEFT_RIGHT)
            elif random_axis == 1:
                return image.transpose(Image.FLIP_TOP_BOTTOM)


class Crop(Operation):
    def __init__(self, probability, width, height, centre):
        Operation.__init__(self, probability)
        self.width = width
        self.height = height
        self.centre = centre

    def perform_operation(self, image):

        w, h = image.size

        if self.centre:
            new_width = self.width / 2.
            new_height = self.height / 2.
            half_the_width = w / 2
            half_the_height = h / 2

            return image.crop(
                (
                    half_the_width - ceil(new_width),
                    half_the_height - ceil(new_height),
                    half_the_width + floor(new_width),
                    half_the_height + floor(new_height)
                )
            )
        else:
            random_right_shift = random.randint(0, (w - self.width))
            random_down_shift = random.randint(0, (h - self.height))

            return image.crop(
                (
                    random_right_shift,
                    random_down_shift,
                    self.width+random_right_shift,
                    self.height+random_down_shift
                )
            )


class CropPercentage(Operation):
    def __init__(self, probability, percentage_area, centre):
        Operation.__init__(self, probability)
        self.percentage_area = percentage_area
        self.centre = centre

    def perform_operation(self, image):
        w, h = image.size
        w_new = int(floor(w * self.percentage_area))  # TODO: Floor might return 0, so we need to check this.
        h_new = int(floor(h * self.percentage_area))

        if self.centre:
            left_shift = floor(w_new / 2.)
            down_shift = floor(h_new / 2.)
            return image.crop((left_shift, down_shift, w_new + left_shift, h_new + down_shift))
        else:
            random_left_shift = random.randint(0, (w - w_new))  # Note: randint() is from uniform distribution.
            random_down_shift = random.randint(0, (h - h_new))
            return image.crop((random_left_shift, random_down_shift, w_new + random_left_shift, h_new + random_down_shift))


class CropRandom(Operation):
    def __init__(self, probability, percentage_area):
        Operation.__init__(self, probability)
        self.percentage_area = percentage_area

    def perform_operation(self, image):
        w, h = image.size

        # TODO: Fix this, as it is currently 1/4 of the area for 0.5 rather than 1/2.
        w_new = int(floor(w * self.percentage_area))  # TODO: Floor might return 0, so we need to check this.
        h_new = int(floor(h * self.percentage_area))

        random_left_shift = random.randint(0, (w - w_new))  # Note: randint() is from uniform distribution.
        random_down_shift = random.randint(0, (h - h_new))

        return image.crop((random_left_shift, random_down_shift, w_new + random_left_shift, h_new + random_down_shift))


class Shear(Operation):
    def __init__(self, probability, max_shear_left, max_shear_right):
        Operation.__init__(self, probability)
        # This is in radians, see
        # http://scikit-image.org/docs/dev/api/skimage.transform.html
        self.max_shear_left = max_shear_left
        self.max_shear_right = max_shear_right

    def perform_operation(self, image):

        ######################################################################
        # Old version which uses SciKit Image
        ######################################################################
        # We will use scikit-image for this so first convert to a matrix
        # using NumPy
        # amount_to_shear = round(random.uniform(self.max_shear_left, self.max_shear_right), 2)
        # image_array = np.array(image)
        # And here we are using SciKit Image's `transform` class.
        # shear_transformer = transform.AffineTransform(shear=amount_to_shear)
        # image_sheared = transform.warp(image_array, shear_transformer)
        #
        # Because of warnings
        # with warnings.catch_warnings():
        #     warnings.simplefilter("ignore")
        #     return Image.fromarray(img_as_ubyte(image_sheared))
        ######################################################################

        width, height = image.size

        max_shear_left = -20
        max_shear_right = 20

        angle_to_shear = int(random.uniform(max_shear_left - 1, max_shear_right + 1))
        if angle_to_shear != -1: angle_to_shear += 1

        # We use the angle phi in radians later
        phi = math.tan(math.radians(angle_to_shear))

        # Alternative method
        # Calculate our offset when cropping
        # We know one angle, phi (angle_to_shear)
        # We known theta = 180-90-phi
        # We know one side, opposite (height of image)
        # Adjacent is therefore:
        # tan(theta) = opposite / adjacent
        # A = opposite / tan(theta)
        # theta = math.radians(180-90-angle_to_shear)
        # A = height / math.tan(theta)

        # Transformation matrices can be found here:
        # https://en.wikipedia.org/wiki/Transformation_matrix
        # The PIL affine transform expects the first two rows of
        # any of the affine transformation matrices, seen here:
        # https://en.wikipedia.org/wiki/Transformation_matrix#/media/File:2D_affine_transformation_matrix.svg

        directions = ["x", "y"]
        direction = random.choice(directions)

        if direction == "x":
            # Here we need the unknown b, where a is
            # the height of the image and phi is the
            # angle we want to shear (our knowns):
            # b = tan(phi) * a
            shift_in_pixels = phi * height

            if shift_in_pixels > 0:
                shift_in_pixels = math.ceil(shift_in_pixels)
            else:
                shift_in_pixels = math.floor(shift_in_pixels)

            # For negative tilts, we reverse phi and set offset to 0
            # Also matrix offset differs from pixel shift for neg
            # but not for pos so we will copy this value in case
            # we need to change it
            matrix_offset = shift_in_pixels
            if angle_to_shear <= 0:
                shift_in_pixels = abs(shift_in_pixels)
                matrix_offset = 0
                phi = abs(phi) * -1

            # Note: PIL expects the inverse scale, so 1/scale_factor for example.
            transform_matrix = (1, phi, -matrix_offset,
                                0, 1, 0)

            image = image.transform((int(round(width + shift_in_pixels)), height),
                                    Image.AFFINE,
                                    transform_matrix,
                                    Image.BICUBIC)

            image = image.crop((abs(shift_in_pixels), 0, width, height))

            return image.resize((width, height), resample=Image.BICUBIC)

        elif direction == "y":
            shift_in_pixels = phi * width

            matrix_offset = shift_in_pixels
            if angle_to_shear <= 0:
                shift_in_pixels = abs(shift_in_pixels)
                matrix_offset = 0
                phi = abs(phi) * -1

            transform_matrix = (1, 0, 0,
                                phi, 1, -matrix_offset)

            image = image.transform((width, int(round(height + shift_in_pixels))),
                                    Image.AFFINE,
                                    transform_matrix,
                                    Image.BICUBIC)

            image = image.crop((0, abs(shift_in_pixels), width, height))

            return image.resize((width, height), resample=Image.BICUBIC)


class Scale(Operation):
    """
    Class to increase or decrease images by a certain factor. The ``Resize`` class handles images \
    that need to be re-sized with different **dimensions**, which may not maintain aspect ratio.
    """
    def __init__(self, probability, scale_factor):
        Operation.__init__(self, probability)
        self.scale_factor = scale_factor

    # Resize by a certain factor (*not* dimensions - which would uniformly resize all
    # images to X*Y while scale depends on the size of the input)
    def perform_operation(self, image):
        h, w = image.size
        new_h = h * int(floor(self.scale_factor))
        new_w = w * int(floor(self.scale_factor))
        return image.resize((new_w, new_h))


class Distort(Operation):
    def __init__(self, probability, grid_width, grid_height, magnitude, randomise_magnitude):
        Operation.__init__(self, probability)
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.magnitude = abs(magnitude)
        randomise_magnitude = True  # TODO: Fix code below to handle FALSE state.
        self.randomise_magnitude = randomise_magnitude

    def perform_operation(self, image):

        w, h = image.size

        horizontal_tiles = self.grid_width
        vertical_tiles = self.grid_height

        width_of_square = int(floor(w / float(horizontal_tiles)))
        height_of_square = int(floor(h / float(vertical_tiles)))

        width_of_last_square = w - (width_of_square * (horizontal_tiles - 1))
        height_of_last_square = h - (height_of_square * (vertical_tiles - 1))

        dimensions = []

        for vertical_tile in range(vertical_tiles):
            for horizontal_tile in range(horizontal_tiles):
                if vertical_tile == (vertical_tiles - 1) and horizontal_tile == (horizontal_tiles - 1):
                    dimensions.append([horizontal_tile * width_of_square,
                                       vertical_tile * height_of_square,
                                       width_of_last_square + (horizontal_tile * width_of_square),
                                       height_of_last_square + (height_of_square * vertical_tile)])
                elif vertical_tile == (vertical_tiles - 1):
                    dimensions.append([horizontal_tile * width_of_square,
                                       vertical_tile * height_of_square,
                                       width_of_square + (horizontal_tile * width_of_square),
                                       height_of_last_square + (height_of_square * vertical_tile)])
                elif horizontal_tile == (horizontal_tiles - 1):
                    dimensions.append([horizontal_tile * width_of_square,
                                       vertical_tile * height_of_square,
                                       width_of_last_square + (horizontal_tile * width_of_square),
                                       height_of_square + (height_of_square * vertical_tile)])
                else:
                    dimensions.append([horizontal_tile * width_of_square,
                                       vertical_tile * height_of_square,
                                       width_of_square + (horizontal_tile * width_of_square),
                                       height_of_square + (height_of_square * vertical_tile)])

        # For loop that generates polygons could be rewritten, but maybe harder to read?
        # polygons = [x1,y1, x1,y2, x2,y2, x2,y1 for x1,y1, x2,y2 in dimensions]

        # last_column = [(horizontal_tiles - 1) + horizontal_tiles * i for i in range(vertical_tiles)]
        last_column = []
        for i in range(vertical_tiles):
            last_column.append((horizontal_tiles-1)+horizontal_tiles*i)

        last_row = range((horizontal_tiles * vertical_tiles) - horizontal_tiles, horizontal_tiles * vertical_tiles)

        polygons = []
        for x1, y1, x2, y2 in dimensions:
            polygons.append([x1, y1, x1, y2, x2, y2, x2, y1])

        polygon_indices = []
        for i in range((vertical_tiles * horizontal_tiles) - 1):
            if i not in last_row and i not in last_column:
                polygon_indices.append([i, i + 1, i + horizontal_tiles, i + 1 + horizontal_tiles])

        for a, b, c, d in polygon_indices:
            dx = random.randint(-self.magnitude, self.magnitude)
            dy = random.randint(-self.magnitude, self.magnitude)

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[a]
            polygons[a] = [x1, y1,
                           x2, y2,
                           x3 + dx, y3 + dy,
                           x4, y4]

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[b]
            polygons[b] = [x1, y1,
                           x2 + dx, y2 + dy,
                           x3, y3,
                           x4, y4]

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[c]
            polygons[c] = [x1, y1,
                           x2, y2,
                           x3, y3,
                           x4 + dx, y4 + dy]

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[d]
            polygons[d] = [x1 + dx, y1 + dy,
                           x2, y2,
                           x3, y3,
                           x4, y4]

        generated_mesh = []
        for i in range(len(dimensions)):
            generated_mesh.append([dimensions[i], polygons[i]])

        return image.transform(image.size, Image.MESH, generated_mesh, resample=Image.BICUBIC)


class Zoom(Operation):
    # TODO: Zoom dimensions and do not crop, so that the crop can be applied manually later
    def __init__(self, probability, min_factor, max_factor):
        Operation.__init__(self, probability)
        self.min_factor = min_factor
        self.max_factor = max_factor

    def perform_operation(self, image):
        factor = round(random.uniform(self.min_factor, self.max_factor), 2)
        original_width, original_height = image.size
        # TODO: Join these two functions together so that we don't have this image_zoom variable lying around.
        image_zoomed = image.resize((int(round(image.size[0] * factor)), int(round(image.size[1] * factor))))

        # Return the centre of the zoomed image, so that it is the same dimensions as the original image
        half_the_width = image_zoomed.size[0] / 2
        half_the_height = image_zoomed.size[1] / 2
        return image_zoomed.crop(
            (
                half_the_width - ceil((original_width / 2.)),
                half_the_height - ceil((original_height / 2.)),
                half_the_width + floor((original_width / 2.)),
                half_the_height + floor((original_height / 2.))
            )
        )


class Custom(Operation):
    """
    Class that allows for a custom operations to be performed using Augmentor's
    standard :class:`~Augmentor.Pipeline.Pipeline` object.
    """
    def __init__(self, probability, custom_function, **function_arguments):
        """
        Creates a custom operation that can be added to a pipeline.

        To add a custom operation you can instantiate this class, passing
        a function pointer, :attr:`custom_function`, followed by an
        arbitrarily long list keyword arguments, :attr:`**function_arguments`.

        .. seealso:: The :func:`~Augmentor.Pipeline.Pipeline.add_operation`
         function.

        :param probability: The probability that the operation will be
         performed.
        :param custom_function: The name of the function that performs your
         custom code. Must return an Image object and accept an Image object
         as its first parameter.
        :param function_arguments: The arguments for your custom operation's
         code.
        :type probability: Float
        :type custom_function: *Function
        :type function_arguments: dict
        """
        Operation.__init__(self, probability)
        self.custom_function = custom_function
        self.function_arguments = function_arguments

    def __str__(self):
        return "Custom (" + self.custom_function.__name__ + ")"

    def perform_operation(self, image):
        return self.function_name(image, **self.function_arguments)

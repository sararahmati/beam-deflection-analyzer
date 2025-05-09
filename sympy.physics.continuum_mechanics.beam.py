"""
This module can be used to solve 2D beam bending problems with
singularity functions in mechanics.
"""

from sympy.core import S, Symbol, diff, symbols
from sympy.core.add import Add
from sympy.core.expr import Expr
from sympy.core.function import (Derivative, Function)
from sympy.core.mul import Mul
from sympy.core.relational import Eq
from sympy.core.sympify import sympify
from sympy.solvers import linsolve
from sympy.solvers.ode.ode import dsolve
from sympy.solvers.solvers import solve
from sympy.printing import sstr
from sympy.functions import SingularityFunction, Piecewise, factorial
from sympy.integrals import integrate
from sympy.series import limit
from sympy.plotting import plot, PlotGrid
from sympy.geometry.entity import GeometryEntity
from sympy.external import import_module
from sympy.sets.sets import Interval
from sympy.utilities.lambdify import lambdify
from sympy.utilities.decorator import doctest_depends_on
from sympy.utilities.iterables import iterable

numpy = import_module('numpy', import_kwargs={'fromlist':['arange']})



class Beam:
    def __init__(self, length, elastic_modulus, second_moment, area=Symbol('A'), variable=Symbol('x'), base_char='C'):
        """Initializes the class.

        Parameters
        ==========

        length : Sympifyable
            A Symbol or value representing the Beam's length.

        elastic_modulus : Sympifyable
            A SymPy expression representing the Beam's Modulus of Elasticity.
            It is a measure of the stiffness of the Beam material. It can
            also be a continuous function of position along the beam.

        second_moment : Sympifyable or Geometry object
            Describes the cross-section of the beam via a SymPy expression
            representing the Beam's second moment of area. It is a geometrical
            property of an area which reflects how its points are distributed
            with respect to its neutral axis. It can also be a continuous
            function of position along the beam. Alternatively ``second_moment``
            can be a shape object such as a ``Polygon`` from the geometry module
            representing the shape of the cross-section of the beam. In such cases,
            it is assumed that the x-axis of the shape object is aligned with the
            bending axis of the beam. The second moment of area will be computed
            from the shape object internally.

        area : Symbol/float
            Represents the cross-section area of beam

        variable : Symbol, optional
            A Symbol object that will be used as the variable along the beam
            while representing the load, shear, moment, slope and deflection
            curve. By default, it is set to ``Symbol('x')``.

        base_char : String, optional
            A String that will be used as base character to generate sequential
            symbols for integration constants in cases where boundary conditions
            are not sufficient to solve them.
        """
        self.length = length
        self.elastic_modulus = elastic_modulus
        if isinstance(second_moment, GeometryEntity):
            self.cross_section = second_moment
        else:
            self.cross_section = None
            self.second_moment = second_moment
        self.variable = variable
        self._base_char = base_char
        self._boundary_conditions = {'deflection': [], 'slope': []}
        self._load = 0
        self._area = area
        self._applied_supports = []
        self._support_as_loads = []
        self._applied_loads = []
        self._reaction_loads = {}
        self._ild_reactions = {}
        self._ild_shear = 0
        self._ild_moment = 0
        # _original_load is a copy of _load equations with unsubstituted reaction
        # forces. It is used for calculating reaction forces in case of I.L.D.
        self._original_load = 0
        self._composite_type = None
        self._hinge_position = None

    def __str__(self):
        shape_description = self._cross_section if self._cross_section else self._second_moment
        str_sol = 'Beam({}, {}, {})'.format(sstr(self._length), sstr(self._elastic_modulus), sstr(shape_description))
        return str_sol

    @property
    def reaction_loads(self):
        """ Returns the reaction forces in a dictionary."""
        return self._reaction_loads

    @property
    def ild_shear(self):
        """ Returns the I.L.D. shear equation."""
        return self._ild_shear

    @property
    def ild_reactions(self):
        """ Returns the I.L.D. reaction forces in a dictionary."""
        return self._ild_reactions

    @property
    def ild_moment(self):
        """ Returns the I.L.D. moment equation."""
        return self._ild_moment

    @property
    def length(self):
        """Length of the Beam."""
        return self._length

    @length.setter
    def length(self, l):
        self._length = sympify(l)

    @property
    def area(self):
        """Cross-sectional area of the Beam. """
        return self._area

    @area.setter
    def area(self, a):
        self._area = sympify(a)

    @property
    def variable(self):
        """
        A symbol that can be used as a variable along the length of the beam
        while representing load distribution, shear force curve, bending
        moment, slope curve and the deflection curve. By default, it is set
        to ``Symbol('x')``, but this property is mutable.

        """
        return self._variable

    @variable.setter
    def variable(self, v):
        if isinstance(v, Symbol):
            self._variable = v
        else:
            raise TypeError("""The variable should be a Symbol object.""")

    @property
    def elastic_modulus(self):
        """Young's Modulus of the Beam. """
        return self._elastic_modulus

    @elastic_modulus.setter
    def elastic_modulus(self, e):
        self._elastic_modulus = sympify(e)

    @property
    def second_moment(self):
        """Second moment of area of the Beam. """
        return self._second_moment

    @second_moment.setter
    def second_moment(self, i):
        self._cross_section = None
        if isinstance(i, GeometryEntity):
            raise ValueError("To update cross-section geometry use `cross_section` attribute")
        else:
            self._second_moment = sympify(i)

    @property
    def cross_section(self):
        """Cross-section of the beam"""
        return self._cross_section

    @cross_section.setter
    def cross_section(self, s):
        if s:
            self._second_moment = s.second_moment_of_area()[0]
        self._cross_section = s

    @property
    def boundary_conditions(self):
        """
        Returns a dictionary of boundary conditions applied on the beam.
        The dictionary has three keywords namely moment, slope and deflection.
        The value of each keyword is a list of tuple, where each tuple
        contains location and value of a boundary condition in the format
        (location, value).
        """
        return self._boundary_conditions

    @property
    def bc_slope(self):
        return self._boundary_conditions['slope']

    @bc_slope.setter
    def bc_slope(self, s_bcs):
        self._boundary_conditions['slope'] = s_bcs

    @property
    def bc_deflection(self):
        return self._boundary_conditions['deflection']

    @bc_deflection.setter
    def bc_deflection(self, d_bcs):
        self._boundary_conditions['deflection'] = d_bcs

    def join(self, beam, via="fixed"):
        """
        This method joins two beams to make a new composite beam system.
        Passed Beam class instance is attached to the right end of calling
        object. This method can be used to form beams having Discontinuous
        values of Elastic modulus or Second moment.

        Parameters
        ==========
        beam : Beam class object
            The Beam object which would be connected to the right of calling
            object.
        via : String
            States the way two Beam object would get connected
            - For axially fixed Beams, via="fixed"
            - For Beams connected via hinge, via="hinge"
        """
        x = self.variable
        E = self.elastic_modulus
        new_length = self.length + beam.length
        if self.second_moment != beam.second_moment:
            new_second_moment = Piecewise((self.second_moment, x<=self.length),
                                    (beam.second_moment, x<=new_length))
        else:
            new_second_moment = self.second_moment

        if via == "fixed":
            new_beam = Beam(new_length, E, new_second_moment, x)
            new_beam._composite_type = "fixed"
            return new_beam

        if via == "hinge":
            new_beam = Beam(new_length, E, new_second_moment, x)
            new_beam._composite_type = "hinge"
            new_beam._hinge_position = self.length
            return new_beam

    def apply_support(self, loc, type="fixed"):
        """
        This method applies support to a particular beam object.

        Parameters
        ==========
        loc : Sympifyable
            Location of point at which support is applied.
        type : String
            Determines type of Beam support applied. To apply support structure
            with
            - zero degree of freedom, type = "fixed"
            - one degree of freedom, type = "pin"
            - two degrees of freedom, type = "roller"
        """
        loc = sympify(loc)
        self._applied_supports.append((loc, type))
        if type in ("pin", "roller"):
            reaction_load = Symbol('R_'+str(loc))
            self.apply_load(reaction_load, loc, -1)
            self.bc_deflection.append((loc, 0))
        else:
            reaction_load = Symbol('R_'+str(loc))
            reaction_moment = Symbol('M_'+str(loc))
            self.apply_load(reaction_load, loc, -1)
            self.apply_load(reaction_moment, loc, -2)
            self.bc_deflection.append((loc, 0))
            self.bc_slope.append((loc, 0))
            self._support_as_loads.append((reaction_moment, loc, -2, None))

        self._support_as_loads.append((reaction_load, loc, -1, None))

    def apply_load(self, value, start, order, end=None):
        """
        This method adds up the loads given to a particular beam object.

        Parameters
        ==========
        value : Sympifyable
            The value inserted should have the units [Force/(Distance**(n+1)]
            where n is the order of applied load.
            Units for applied loads:

               - For moments, unit = kN*m
               - For point loads, unit = kN
               - For constant distributed load, unit = kN/m
               - For ramp loads, unit = kN/m/m
               - For parabolic ramp loads, unit = kN/m/m/m
               - ... so on.

        start : Sympifyable
            The starting point of the applied load. For point moments and
            point forces this is the location of application.
        order : Integer
            The order of the applied load.

               - For moments, order = -2
               - For point loads, order =-1
               - For constant distributed load, order = 0
               - For ramp loads, order = 1
               - For parabolic ramp loads, order = 2
               - ... so on.

        end : Sympifyable, optional
            An optional argument that can be used if the load has an end point
            within the length of the beam.
        """
        x = self.variable
        value = sympify(value)
        start = sympify(start)
        order = sympify(order)

        self._applied_loads.append((value, start, order, end))
        self._load += value*SingularityFunction(x, start, order)
        self._original_load += value*SingularityFunction(x, start, order)

        if end:
            # load has an end point within the length of the beam.
            self._handle_end(x, value, start, order, end, type="apply")

    def remove_load(self, value, start, order, end=None):
        """
        This method removes a particular load present on the beam object.
        Returns a ValueError if the load passed as an argument is not
        present on the beam.

        Parameters
        ==========
        value : Sympifyable
            The magnitude of an applied load.
        start : Sympifyable
            The starting point of the applied load. For point moments and
            point forces this is the location of application.
        order : Integer
            The order of the applied load.
            - For moments, order= -2
            - For point loads, order=-1
            - For constant distributed load, order=0
            - For ramp loads, order=1
            - For parabolic ramp loads, order=2
            - ... so on.
        end : Sympifyable, optional
            An optional argument that can be used if the load has an end point
            within the length of the beam.
        """
        x = self.variable
        value = sympify(value)
        start = sympify(start)
        order = sympify(order)

        if (value, start, order, end) in self._applied_loads:
            self._load -= value*SingularityFunction(x, start, order)
            self._original_load -= value*SingularityFunction(x, start, order)
            self._applied_loads.remove((value, start, order, end))
        else:
            msg = "No such load distribution exists on the beam object."
            raise ValueError(msg)

        if end:
            # load has an end point within the length of the beam.
            self._handle_end(x, value, start, order, end, type="remove")

    def _handle_end(self, x, value, start, order, end, type):
        """
        This functions handles the optional `end` value in the
        `apply_load` and `remove_load` functions. When the value
        of end is not NULL, this function will be executed.
        """
        if order.is_negative:
            msg = ("If 'end' is provided the 'order' of the load cannot "
                    "be negative, i.e. 'end' is only valid for distributed "
                    "loads.")
            raise ValueError(msg)
        # NOTE : A Taylor series can be used to define the summation of
        # singularity functions that subtract from the load past the end
        # point such that it evaluates to zero past 'end'.
        f = value*x**order

        if type == "apply":
            # iterating for "apply_load" method
            for i in range(0, order + 1):
                self._load -= (f.diff(x, i).subs(x, end - start) *
                                SingularityFunction(x, end, i)/factorial(i))
                self._original_load -= (f.diff(x, i).subs(x, end - start) *
                                SingularityFunction(x, end, i)/factorial(i))
        elif type == "remove":
            # iterating for "remove_load" method
            for i in range(0, order + 1):
                self._load += (f.diff(x, i).subs(x, end - start) *
                                SingularityFunction(x, end, i)/factorial(i))
                self._original_load += (f.diff(x, i).subs(x, end - start) *
                                SingularityFunction(x, end, i)/factorial(i))


    @property
    def load(self):
        """
        Returns a Singularity Function expression which represents
        the load distribution curve of the Beam object.
        """
        return self._load

    @property
    def applied_loads(self):
        """
        Returns a list of all loads applied on the beam object.
        Each load in the list is a tuple of form (value, start, order, end).
        """
        return self._applied_loads

    def _solve_hinge_beams(self, *reactions):
        """Method to find integration constants and reactional variables in a
        composite beam connected via hinge.
        This method resolves the composite Beam into its sub-beams and then
        equations of shear force, bending moment, slope and deflection are
        evaluated for both of them separately. These equations are then solved
        for unknown reactions and integration constants using the boundary
        conditions applied on the Beam. Equal deflection of both sub-beams
        at the hinge joint gives us another equation to solve the system.
        """
        x = self.variable
        l = self._hinge_position
        E = self._elastic_modulus
        I = self._second_moment

        if isinstance(I, Piecewise):
            I1 = I.args[0][0]
            I2 = I.args[1][0]
        else:
            I1 = I2 = I

        load_1 = 0       # Load equation on first segment of composite beam
        load_2 = 0       # Load equation on second segment of composite beam

        # Distributing load on both segments
        for load in self.applied_loads:
            if load[1] < l:
                load_1 += load[0]*SingularityFunction(x, load[1], load[2])
                if load[2] == 0:
                    load_1 -= load[0]*SingularityFunction(x, load[3], load[2])
                elif load[2] > 0:
                    load_1 -= load[0]*SingularityFunction(x, load[3], load[2]) + load[0]*SingularityFunction(x, load[3], 0)
            elif load[1] == l:
                load_1 += load[0]*SingularityFunction(x, load[1], load[2])
                load_2 += load[0]*SingularityFunction(x, load[1] - l, load[2])
            elif load[1] > l:
                load_2 += load[0]*SingularityFunction(x, load[1] - l, load[2])
                if load[2] == 0:
                    load_2 -= load[0]*SingularityFunction(x, load[3] - l, load[2])
                elif load[2] > 0:
                    load_2 -= load[0]*SingularityFunction(x, load[3] - l, load[2]) + load[0]*SingularityFunction(x, load[3] - l, 0)

        h = Symbol('h')     # Force due to hinge
        load_1 += h*SingularityFunction(x, l, -1)
        load_2 -= h*SingularityFunction(x, 0, -1)

        eq = []
        shear_1 = integrate(load_1, x)
        shear_curve_1 = limit(shear_1, x, l)
        eq.append(shear_curve_1)
        bending_1 = integrate(shear_1, x)
        moment_curve_1 = limit(bending_1, x, l)
        eq.append(moment_curve_1)

        shear_2 = integrate(load_2, x)
        shear_curve_2 = limit(shear_2, x, self.length - l)
        eq.append(shear_curve_2)
        bending_2 = integrate(shear_2, x)
        moment_curve_2 = limit(bending_2, x, self.length - l)
        eq.append(moment_curve_2)

        C1 = Symbol('C1')
        C2 = Symbol('C2')
        C3 = Symbol('C3')
        C4 = Symbol('C4')
        slope_1 = S.One/(E*I1)*(integrate(bending_1, x) + C1)
        def_1 = S.One/(E*I1)*(integrate((E*I)*slope_1, x) + C1*x + C2)
        slope_2 = S.One/(E*I2)*(integrate(integrate(integrate(load_2, x), x), x) + C3)
        def_2 = S.One/(E*I2)*(integrate((E*I)*slope_2, x) + C4)

        for position, value in self.bc_slope:
            if position<l:
                eq.append(slope_1.subs(x, position) - value)
            else:
                eq.append(slope_2.subs(x, position - l) - value)

        for position, value in self.bc_deflection:
            if position<l:
                eq.append(def_1.subs(x, position) - value)
            else:
                eq.append(def_2.subs(x, position - l) - value)

        eq.append(def_1.subs(x, l) - def_2.subs(x, 0)) # Deflection of both the segments at hinge would be equal

        constants = list(linsolve(eq, C1, C2, C3, C4, h, *reactions))
        reaction_values = list(constants[0])[5:]

        self._reaction_loads = dict(zip(reactions, reaction_values))
        self._load = self._load.subs(self._reaction_loads)

        # Substituting constants and reactional load and moments with their corresponding values
        slope_1 = slope_1.subs({C1: constants[0][0], h:constants[0][4]}).subs(self._reaction_loads)
        def_1 = def_1.subs({C1: constants[0][0], C2: constants[0][1], h:constants[0][4]}).subs(self._reaction_loads)
        slope_2 = slope_2.subs({x: x-l, C3: constants[0][2], h:constants[0][4]}).subs(self._reaction_loads)
        def_2 = def_2.subs({x: x-l,C3: constants[0][2], C4: constants[0][3], h:constants[0][4]}).subs(self._reaction_loads)

        self._hinge_beam_slope = slope_1*SingularityFunction(x, 0, 0) - slope_1*SingularityFunction(x, l, 0) + slope_2*SingularityFunction(x, l, 0)
        self._hinge_beam_deflection = def_1*SingularityFunction(x, 0, 0) - def_1*SingularityFunction(x, l, 0) + def_2*SingularityFunction(x, l, 0)

    def solve_for_reaction_loads(self, *reactions):
        """
        Solves for the reaction forces.
        """
        if self._composite_type == "hinge":
            return self._solve_hinge_beams(*reactions)

        x = self.variable
        l = self.length
        C3 = Symbol('C3')
        C4 = Symbol('C4')

        shear_curve = limit(self.shear_force(), x, l)
        moment_curve = limit(self.bending_moment(), x, l)

        slope_eqs = []
        deflection_eqs = []

        slope_curve = integrate(self.bending_moment(), x) + C3
        for position, value in self._boundary_conditions['slope']:
            eqs = slope_curve.subs(x, position) - value
            slope_eqs.append(eqs)

        deflection_curve = integrate(slope_curve, x) + C4
        for position, value in self._boundary_conditions['deflection']:
            eqs = deflection_curve.subs(x, position) - value
            deflection_eqs.append(eqs)

        solution = list((linsolve([shear_curve, moment_curve] + slope_eqs
                            + deflection_eqs, (C3, C4) + reactions).args)[0])
        solution = solution[2:]

        self._reaction_loads = dict(zip(reactions, solution))
        self._load = self._load.subs(self._reaction_loads)

    def shear_force(self):
        """
        Returns a Singularity Function expression which represents
        the shear force curve of the Beam object.

        """
        x = self.variable
        return -integrate(self.load, x)

    def max_shear_force(self):
        """Returns maximum Shear force and its coordinate
        in the Beam object."""
        shear_curve = self.shear_force()
        x = self.variable

        terms = shear_curve.args
        singularity = []        # Points at which shear function changes
        for term in terms:
            if isinstance(term, Mul):
                term = term.args[-1]    # SingularityFunction in the term
            singularity.append(term.args[1])
        singularity.sort()
        singularity = list(set(singularity))

        intervals = []    # List of Intervals with discrete value of shear force
        shear_values = []   # List of values of shear force in each interval
        for i, s in enumerate(singularity):
            if s == 0:
                continue
            try:
                shear_slope = Piecewise((float("nan"), x<=singularity[i-1]),(self._load.rewrite(Piecewise), x<s), (float("nan"), True))
                points = solve(shear_slope, x)
                val = []
                for point in points:
                    val.append(abs(shear_curve.subs(x, point)))
                points.extend([singularity[i-1], s])
                val += [abs(limit(shear_curve, x, singularity[i-1], '+')), abs(limit(shear_curve, x, s, '-'))]
                max_shear = max(val)
                shear_values.append(max_shear)
                intervals.append(points[val.index(max_shear)])
            # If shear force in a particular Interval has zero or constant
            # slope, then above block gives NotImplementedError as
            # solve can't represent Interval solutions.
            except NotImplementedError:
                initial_shear = limit(shear_curve, x, singularity[i-1], '+')
                final_shear = limit(shear_curve, x, s, '-')
                # If shear_curve has a constant slope(it is a line).
                if shear_curve.subs(x, (singularity[i-1] + s)/2) == (initial_shear + final_shear)/2 and initial_shear != final_shear:
                    shear_values.extend([initial_shear, final_shear])
                    intervals.extend([singularity[i-1], s])
                else:    # shear_curve has same value in whole Interval
                    shear_values.append(final_shear)
                    intervals.append(Interval(singularity[i-1], s))

        shear_values = list(map(abs, shear_values))
        maximum_shear = max(shear_values)
        point = intervals[shear_values.index(maximum_shear)]
        return (point, maximum_shear)

    def bending_moment(self):
        """
        Returns a Singularity Function expression which represents
        the bending moment curve of the Beam object.

        """
        x = self.variable
        return integrate(self.shear_force(), x)

    def max_bmoment(self):
        """Returns maximum Shear force and its coordinate
        in the Beam object."""
        bending_curve = self.bending_moment()
        x = self.variable

        terms = bending_curve.args
        singularity = []        # Points at which bending moment changes
        for term in terms:
            if isinstance(term, Mul):
                term = term.args[-1]    # SingularityFunction in the term
            singularity.append(term.args[1])
        singularity.sort()
        singularity = list(set(singularity))

        intervals = []    # List of Intervals with discrete value of bending moment
        moment_values = []   # List of values of bending moment in each interval
        for i, s in enumerate(singularity):
            if s == 0:
                continue
            try:
                moment_slope = Piecewise((float("nan"), x<=singularity[i-1]),(self.shear_force().rewrite(Piecewise), x<s), (float("nan"), True))
                points = solve(moment_slope, x)
                val = []
                for point in points:
                    val.append(abs(bending_curve.subs(x, point)))
                points.extend([singularity[i-1], s])
                val += [abs(limit(bending_curve, x, singularity[i-1], '+')), abs(limit(bending_curve, x, s, '-'))]
                max_moment = max(val)
                moment_values.append(max_moment)
                intervals.append(points[val.index(max_moment)])
            # If bending moment in a particular Interval has zero or constant
            # slope, then above block gives NotImplementedError as solve
            # can't represent Interval solutions.
            except NotImplementedError:
                initial_moment = limit(bending_curve, x, singularity[i-1], '+')
                final_moment = limit(bending_curve, x, s, '-')
                # If bending_curve has a constant slope(it is a line).
                if bending_curve.subs(x, (singularity[i-1] + s)/2) == (initial_moment + final_moment)/2 and initial_moment != final_moment:
                    moment_values.extend([initial_moment, final_moment])
                    intervals.extend([singularity[i-1], s])
                else:    # bending_curve has same value in whole Interval
                    moment_values.append(final_moment)
                    intervals.append(Interval(singularity[i-1], s))

        moment_values = list(map(abs, moment_values))
        maximum_moment = max(moment_values)
        point = intervals[moment_values.index(maximum_moment)]
        return (point, maximum_moment)

    def point_cflexure(self):
        """
        Returns a Set of point(s) with zero bending moment and
        where bending moment curve of the beam object changes
        its sign from negative to positive or vice versa.
        """

        # To restrict the range within length of the Beam
        moment_curve = Piecewise((float("nan"), self.variable<=0),
                (self.bending_moment(), self.variable<self.length),
                (float("nan"), True))

        points = solve(moment_curve.rewrite(Piecewise), self.variable,
                        domain=S.Reals)
        return points

    def slope(self):
        """
        Returns a Singularity Function expression which represents
        the slope the elastic curve of the Beam object.
        """
        x = self.variable
        E = self.elastic_modulus
        I = self.second_moment

        if self._composite_type == "hinge":
            return self._hinge_beam_slope
        if not self._boundary_conditions['slope']:
            return diff(self.deflection(), x)
        if isinstance(I, Piecewise) and self._composite_type == "fixed":
            args = I.args
            slope = 0
            prev_slope = 0
            prev_end = 0
            for i in range(len(args)):
                if i != 0:
                    prev_end = args[i-1][1].args[1]
                slope_value = -S.One/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                if i != len(args) - 1:
                    slope += (prev_slope + slope_value)*SingularityFunction(x, prev_end, 0) - \
                        (prev_slope + slope_value)*SingularityFunction(x, args[i][1].args[1], 0)
                else:
                    slope += (prev_slope + slope_value)*SingularityFunction(x, prev_end, 0)
                prev_slope = slope_value.subs(x, args[i][1].args[1])
            return slope

        C3 = Symbol('C3')
        slope_curve = -integrate(S.One/(E*I)*self.bending_moment(), x) + C3

        bc_eqs = []
        for position, value in self._boundary_conditions['slope']:
            eqs = slope_curve.subs(x, position) - value
            bc_eqs.append(eqs)
        constants = list(linsolve(bc_eqs, C3))
        slope_curve = slope_curve.subs({C3: constants[0][0]})
        return slope_curve

    def deflection(self):
        """
        Returns a Singularity Function expression which represents
        the elastic curve or deflection of the Beam object.
        """
        x = self.variable
        E = self.elastic_modulus
        I = self.second_moment
        if self._composite_type == "hinge":
            return self._hinge_beam_deflection
        if not self._boundary_conditions['deflection'] and not self._boundary_conditions['slope']:
            if isinstance(I, Piecewise) and self._composite_type == "fixed":
                args = I.args
                prev_slope = 0
                prev_def = 0
                prev_end = 0
                deflection = 0
                for i in range(len(args)):
                    if i != 0:
                        prev_end = args[i-1][1].args[1]
                    slope_value = -S.One/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                    recent_segment_slope = prev_slope + slope_value
                    deflection_value = integrate(recent_segment_slope, (x, prev_end, x))
                    if i != len(args) - 1:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0) \
                            - (prev_def + deflection_value)*SingularityFunction(x, args[i][1].args[1], 0)
                    else:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0)
                    prev_slope = slope_value.subs(x, args[i][1].args[1])
                    prev_def = deflection_value.subs(x, args[i][1].args[1])
                return deflection
            base_char = self._base_char
            constants = symbols(base_char + '3:5')
            return S.One/(E*I)*integrate(-integrate(self.bending_moment(), x), x) + constants[0]*x + constants[1]
        elif not self._boundary_conditions['deflection']:
            base_char = self._base_char
            constant = symbols(base_char + '4')
            return integrate(self.slope(), x) + constant
        elif not self._boundary_conditions['slope'] and self._boundary_conditions['deflection']:
            if isinstance(I, Piecewise) and self._composite_type == "fixed":
                args = I.args
                prev_slope = 0
                prev_def = 0
                prev_end = 0
                deflection = 0
                for i in range(len(args)):
                    if i != 0:
                        prev_end = args[i-1][1].args[1]
                    slope_value = -S.One/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                    recent_segment_slope = prev_slope + slope_value
                    deflection_value = integrate(recent_segment_slope, (x, prev_end, x))
                    if i != len(args) - 1:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0) \
                            - (prev_def + deflection_value)*SingularityFunction(x, args[i][1].args[1], 0)
                    else:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0)
                    prev_slope = slope_value.subs(x, args[i][1].args[1])
                    prev_def = deflection_value.subs(x, args[i][1].args[1])
                return deflection
            base_char = self._base_char
            C3, C4 = symbols(base_char + '3:5')    # Integration constants
            slope_curve = -integrate(self.bending_moment(), x) + C3
            deflection_curve = integrate(slope_curve, x) + C4
            bc_eqs = []
            for position, value in self._boundary_conditions['deflection']:
                eqs = deflection_curve.subs(x, position) - value
                bc_eqs.append(eqs)
            constants = list(linsolve(bc_eqs, (C3, C4)))
            deflection_curve = deflection_curve.subs({C3: constants[0][0], C4: constants[0][1]})
            return S.One/(E*I)*deflection_curve

        if isinstance(I, Piecewise) and self._composite_type == "fixed":
            args = I.args
            prev_slope = 0
            prev_def = 0
            prev_end = 0
            deflection = 0
            for i in range(len(args)):
                if i != 0:
                    prev_end = args[i-1][1].args[1]
                slope_value = S.One/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                recent_segment_slope = prev_slope + slope_value
                deflection_value = integrate(recent_segment_slope, (x, prev_end, x))
                if i != len(args) - 1:
                    deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0) \
                        - (prev_def + deflection_value)*SingularityFunction(x, args[i][1].args[1], 0)
                else:
                    deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0)
                prev_slope = slope_value.subs(x, args[i][1].args[1])
                prev_def = deflection_value.subs(x, args[i][1].args[1])
            return deflection

        C4 = Symbol('C4')
        deflection_curve = integrate(self.slope(), x) + C4

        bc_eqs = []
        for position, value in self._boundary_conditions['deflection']:
            eqs = deflection_curve.subs(x, position) - value
            bc_eqs.append(eqs)

        constants = list(linsolve(bc_eqs, C4))
        deflection_curve = deflection_curve.subs({C4: constants[0][0]})
        return deflection_curve

    def max_deflection(self):
        """
        Returns point of max deflection and its corresponding deflection value
        in a Beam object.
        """

        # To restrict the range within length of the Beam
        slope_curve = Piecewise((float("nan"), self.variable<=0),
                (self.slope(), self.variable<self.length),
                (float("nan"), True))

        points = solve(slope_curve.rewrite(Piecewise), self.variable,
                        domain=S.Reals)
        deflection_curve = self.deflection()
        deflections = [deflection_curve.subs(self.variable, x) for x in points]
        deflections = list(map(abs, deflections))
        if len(deflections) != 0:
            max_def = max(deflections)
            return (points[deflections.index(max_def)], max_def)
        else:
            return None

    def shear_stress(self):
        """
        Returns an expression representing the Shear Stress
        curve of the Beam object.
        """
        return self.shear_force()/self._area

    def plot_shear_stress(self, subs=None):
        """

        Returns a plot of shear stress present in the beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.
        """

        shear_stress = self.shear_stress()
        x = self.variable
        length = self.length

        if subs is None:
            subs = {}
        for sym in shear_stress.atoms(Symbol):
            if sym != x and sym not in subs:
                raise ValueError('value of %s was not passed.' %sym)

        if length in subs:
            length = subs[length]

        # Returns Plot of Shear Stress
        return plot (shear_stress.subs(subs), (x, 0, length),
        title='Shear Stress', xlabel=r'$\mathrm{x}$', ylabel=r'$\tau$',
        line_color='r')


    def plot_shear_force(self, subs=None):
        """

        Returns a plot for Shear force present in the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.
        """
        shear_force = self.shear_force()
        if subs is None:
            subs = {}
        for sym in shear_force.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(shear_force.subs(subs), (self.variable, 0, length), title='Shear Force',
                xlabel=r'$\mathrm{x}$', ylabel=r'$\mathrm{V}$', line_color='g')

    def plot_bending_moment(self, subs=None):
        """

        Returns a plot for Bending moment present in the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.
        """
        bending_moment = self.bending_moment()
        if subs is None:
            subs = {}
        for sym in bending_moment.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(bending_moment.subs(subs), (self.variable, 0, length), title='Bending Moment',
                xlabel=r'$\mathrm{x}$', ylabel=r'$\mathrm{M}$', line_color='b')

    def plot_slope(self, subs=None):
        """

        Returns a plot for slope of deflection curve of the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.
        """
        slope = self.slope()
        if subs is None:
            subs = {}
        for sym in slope.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(slope.subs(subs), (self.variable, 0, length), title='Slope',
                xlabel=r'$\mathrm{x}$', ylabel=r'$\theta$', line_color='m')

    def plot_deflection(self, subs=None):
        """

        Returns a plot for deflection curve of the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.
        """
        deflection = self.deflection()
        if subs is None:
            subs = {}
        for sym in deflection.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(deflection.subs(subs), (self.variable, 0, length),
                    title='Deflection', xlabel=r'$\mathrm{x}$', ylabel=r'$\delta$',
                    line_color='r')


    def plot_loading_results(self, subs=None):
        """
        Returns a subplot of Shear Force, Bending Moment,
        Slope and Deflection of the Beam object.

        Parameters
        ==========

        subs : dictionary
               Python dictionary containing Symbols as key and their
               corresponding values.
        """
        length = self.length
        variable = self.variable
        if subs is None:
            subs = {}
        for sym in self.deflection().atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if length in subs:
            length = subs[length]
        ax1 = plot(self.shear_force().subs(subs), (variable, 0, length),
                   title="Shear Force", xlabel=r'$\mathrm{x}$', ylabel=r'$\mathrm{V}$',
                   line_color='g', show=False)
        ax2 = plot(self.bending_moment().subs(subs), (variable, 0, length),
                   title="Bending Moment", xlabel=r'$\mathrm{x}$', ylabel=r'$\mathrm{M}$',
                   line_color='b', show=False)
        ax3 = plot(self.slope().subs(subs), (variable, 0, length),
                   title="Slope", xlabel=r'$\mathrm{x}$', ylabel=r'$\theta$',
                   line_color='m', show=False)
        ax4 = plot(self.deflection().subs(subs), (variable, 0, length),
                   title="Deflection", xlabel=r'$\mathrm{x}$', ylabel=r'$\delta$',
                   line_color='r', show=False)

        return PlotGrid(4, 1, ax1, ax2, ax3, ax4)

    def _solve_for_ild_equations(self):
        """

        Helper function for I.L.D. It takes the unsubstituted
        copy of the load equation and uses it to calculate shear force and bending
        moment equations.
        """

        x = self.variable
        shear_force = -integrate(self._original_load, x)
        bending_moment = integrate(shear_force, x)

        return shear_force, bending_moment

    def solve_for_ild_reactions(self, value, *reactions):
        """

        Determines the Influence Line Diagram equations for reaction
        forces under the effect of a moving load.

        Parameters
        ==========
        value : Integer
            Magnitude of moving load
        reactions :
            The reaction forces applied on the beam.
        """
        shear_force, bending_moment = self._solve_for_ild_equations()
        x = self.variable
        l = self.length
        C3 = Symbol('C3')
        C4 = Symbol('C4')

        shear_curve = limit(shear_force, x, l) - value
        moment_curve = limit(bending_moment, x, l) - value*(l-x)

        slope_eqs = []
        deflection_eqs = []

        slope_curve = integrate(bending_moment, x) + C3
        for position, value in self._boundary_conditions['slope']:
            eqs = slope_curve.subs(x, position) - value
            slope_eqs.append(eqs)

        deflection_curve = integrate(slope_curve, x) + C4
        for position, value in self._boundary_conditions['deflection']:
            eqs = deflection_curve.subs(x, position) - value
            deflection_eqs.append(eqs)

        solution = list((linsolve([shear_curve, moment_curve] + slope_eqs
                            + deflection_eqs, (C3, C4) + reactions).args)[0])
        solution = solution[2:]

        # Determining the equations and solving them.
        self._ild_reactions = dict(zip(reactions, solution))

    def plot_ild_reactions(self, subs=None):
        """

        Plots the Influence Line Diagram of Reaction Forces
        under the effect of a moving load. This function
        should be called after calling solve_for_ild_reactions().

        Parameters
        ==========

        subs : dictionary
               Python dictionary containing Symbols as key and their
               corresponding values.
        """
        if not self._ild_reactions:
            raise ValueError("I.L.D. reaction equations not found. Please use solve_for_ild_reactions() to generate the I.L.D. reaction equations.")

        x = self.variable
        ildplots = []

        if subs is None:
            subs = {}

        for reaction in self._ild_reactions:
            for sym in self._ild_reactions[reaction].atoms(Symbol):
                if sym != x and sym not in subs:
                    raise ValueError('Value of %s was not passed.' %sym)

        for sym in self._length.atoms(Symbol):
            if sym != x and sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)

        for reaction in self._ild_reactions:
            ildplots.append(plot(self._ild_reactions[reaction].subs(subs),
            (x, 0, self._length.subs(subs)), title='I.L.D. for Reactions',
            xlabel=x, ylabel=reaction, line_color='blue', show=False))

        return PlotGrid(len(ildplots), 1, *ildplots)

    def solve_for_ild_shear(self, distance, value, *reactions):
        """

        Determines the Influence Line Diagram equations for shear at a
        specified point under the effect of a moving load.

        Parameters
        ==========
        distance : Integer
            Distance of the point from the start of the beam
            for which equations are to be determined
        value : Integer
            Magnitude of moving load
        reactions :
            The reaction forces applied on the beam.
        """

        x = self.variable
        l = self.length

        shear_force, _ = self._solve_for_ild_equations()

        shear_curve1 = value - limit(shear_force, x, distance)
        shear_curve2 = (limit(shear_force, x, l) - limit(shear_force, x, distance)) - value

        for reaction in reactions:
            shear_curve1 = shear_curve1.subs(reaction,self._ild_reactions[reaction])
            shear_curve2 = shear_curve2.subs(reaction,self._ild_reactions[reaction])

        shear_eq = Piecewise((shear_curve1, x < distance), (shear_curve2, x > distance))

        self._ild_shear = shear_eq

    def plot_ild_shear(self,subs=None):
        """

        Plots the Influence Line Diagram for Shear under the effect
        of a moving load. This function should be called after
        calling solve_for_ild_shear().

        Parameters
        ==========

        subs : dictionary
               Python dictionary containing Symbols as key and their
               corresponding values.
        """

        if not self._ild_shear:
            raise ValueError("I.L.D. shear equation not found. Please use solve_for_ild_shear() to generate the I.L.D. shear equations.")

        x = self.variable
        l = self._length

        if subs is None:
            subs = {}

        for sym in self._ild_shear.atoms(Symbol):
            if sym != x and sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)

        for sym in self._length.atoms(Symbol):
            if sym != x and sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)

        return plot(self._ild_shear.subs(subs), (x, 0, l),  title='I.L.D. for Shear',
               xlabel=r'$\mathrm{X}$', ylabel=r'$\mathrm{V}$', line_color='blue',show=True)

    def solve_for_ild_moment(self, distance, value, *reactions):
        """

        Determines the Influence Line Diagram equations for moment at a
        specified point under the effect of a moving load.

        Parameters
        ==========
        distance : Integer
            Distance of the point from the start of the beam
            for which equations are to be determined
        value : Integer
            Magnitude of moving load
        reactions :
            The reaction forces applied on the beam.
        """

        x = self.variable
        l = self.length

        _, moment = self._solve_for_ild_equations()

        moment_curve1 = value*(distance-x) - limit(moment, x, distance)
        moment_curve2= (limit(moment, x, l)-limit(moment, x, distance))-value*(l-x)

        for reaction in reactions:
            moment_curve1 = moment_curve1.subs(reaction, self._ild_reactions[reaction])
            moment_curve2 = moment_curve2.subs(reaction, self._ild_reactions[reaction])

        moment_eq = Piecewise((moment_curve1, x < distance), (moment_curve2, x > distance))
        self._ild_moment = moment_eq

    def plot_ild_moment(self,subs=None):
        """

        Plots the Influence Line Diagram for Moment under the effect
        of a moving load. This function should be called after
        calling solve_for_ild_moment().

        Parameters
        ==========

        subs : dictionary
               Python dictionary containing Symbols as key and their
               corresponding values.
        """

        if not self._ild_moment:
            raise ValueError("I.L.D. moment equation not found. Please use solve_for_ild_moment() to generate the I.L.D. moment equations.")

        x = self.variable

        if subs is None:
            subs = {}

        for sym in self._ild_moment.atoms(Symbol):
            if sym != x and sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)

        for sym in self._length.atoms(Symbol):
            if sym != x and sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        return plot(self._ild_moment.subs(subs), (x, 0, self._length), title='I.L.D. for Moment',
               xlabel=r'$\mathrm{X}$', ylabel=r'$\mathrm{M}$', line_color='blue', show=True)

    @doctest_depends_on(modules=('numpy',))
    def draw(self, pictorial=True):
        """
        Returns a plot object representing the beam diagram of the beam.

        .. note::
            The user must be careful while entering load values.
            The draw function assumes a sign convention which is used
            for plotting loads.
            Given a right handed coordinate system with XYZ coordinates,
            the beam's length is assumed to be along the positive X axis.
            The draw function recognizes positve loads(with n>-2) as loads
            acting along negative Y direction and positve moments acting
            along positive Z direction.

        Parameters
        ==========

        pictorial: Boolean (default=True)
            Setting ``pictorial=True`` would simply create a pictorial (scaled) view
            of the beam diagram not with the exact dimensions.
            Although setting ``pictorial=False`` would create a beam diagram with
            the exact dimensions on the plot
        """
        if not numpy:
            raise ImportError("To use this function numpy module is required")

        x = self.variable

        # checking whether length is an expression in terms of any Symbol.
        if isinstance(self.length, Expr):
            l = list(self.length.atoms(Symbol))
            # assigning every Symbol a default value of 10
            l = {i:10 for i in l}
            length = self.length.subs(l)
        else:
            l = {}
            length = self.length
        height = length/10

        rectangles = []
        rectangles.append({'xy':(0, 0), 'width':length, 'height': height, 'facecolor':"brown"})
        annotations, markers, load_eq,load_eq1, fill = self._draw_load(pictorial, length, l)
        support_markers, support_rectangles = self._draw_supports(length, l)

        rectangles += support_rectangles
        markers += support_markers

        sing_plot = plot(height + load_eq, height + load_eq1, (x, 0, length),
         xlim=(-height, length + height), ylim=(-length, 1.25*length), annotations=annotations,
          markers=markers, rectangles=rectangles, line_color='brown', fill=fill, axis=False, show=False)

        return sing_plot


    def _draw_load(self, pictorial, length, l):
        loads = list(set(self.applied_loads) - set(self._support_as_loads))
        height = length/10
        x = self.variable

        annotations = []
        markers = []
        load_args = []
        scaled_load = 0
        load_args1 = []
        scaled_load1 = 0
        load_eq = 0     # For positive valued higher order loads
        load_eq1 = 0    # For negative valued higher order loads
        fill = None
        plus = 0        # For positive valued higher order loads
        minus = 0       # For negative valued higher order loads
        for load in loads:

            # check if the position of load is in terms of the beam length.
            if l:
                pos =  load[1].subs(l)
            else:
                pos = load[1]

            # point loads
            if load[2] == -1:
                if isinstance(load[0], Symbol) or load[0].is_negative:
                    annotations.append({'text':'', 'xy':(pos, 0), 'xytext':(pos, height - 4*height), 'arrowprops':dict(width= 1.5, headlength=5, headwidth=5, facecolor='black')})
                else:
                    annotations.append({'text':'', 'xy':(pos, height),  'xytext':(pos, height*4), 'arrowprops':dict(width= 1.5, headlength=4, headwidth=4, facecolor='black')})
            # moment loads
            elif load[2] == -2:
                if load[0].is_negative:
                    markers.append({'args':[[pos], [height/2]], 'marker': r'$\circlearrowright$', 'markersize':15})
                else:
                    markers.append({'args':[[pos], [height/2]], 'marker': r'$\circlearrowleft$', 'markersize':15})
            # higher order loads
            elif load[2] >= 0:
                # `fill` will be assigned only when higher order loads are present
                value, start, order, end = load
                # Positive loads have their seperate equations
                if(value>0):
                    plus = 1
                # if pictorial is True we remake the load equation again with
                # some constant magnitude values.
                    if pictorial:
                        value = 10**(1-order) if order > 0 else length/2
                        scaled_load += value*SingularityFunction(x, start, order)
                        if end:
                            f2 = 10**(1-order)*x**order if order > 0 else length/2*x**order
                            for i in range(0, order + 1):
                                scaled_load -= (f2.diff(x, i).subs(x, end - start)*
                                               SingularityFunction(x, end, i)/factorial(i))

                    if pictorial:
                        if isinstance(scaled_load, Add):
                            load_args = scaled_load.args
                        else:
                            # when the load equation consists of only a single term
                            load_args = (scaled_load,)
                        load_eq = [i.subs(l) for i in load_args]
                    else:
                        if isinstance(self.load, Add):
                            load_args = self.load.args
                        else:
                            load_args = (self.load,)
                        load_eq = [i.subs(l) for i in load_args if list(i.atoms(SingularityFunction))[0].args[2] >= 0]
                    load_eq = Add(*load_eq)

                    # filling higher order loads with colour
                    expr = height + load_eq.rewrite(Piecewise)
                    y1 = lambdify(x, expr, 'numpy')

                # For loads with negative value
                else:
                    minus = 1
                    # if pictorial is True we remake the load equation again with
                    # some constant magnitude values.
                    if pictorial:
                        value = 10**(1-order) if order > 0 else length/2
                        scaled_load1 += value*SingularityFunction(x, start, order)
                        if end:
                            f2 = 10**(1-order)*x**order if order > 0 else length/2*x**order
                            for i in range(0, order + 1):
                                scaled_load1 -= (f2.diff(x, i).subs(x, end - start)*
                                               SingularityFunction(x, end, i)/factorial(i))

                    if pictorial:
                        if isinstance(scaled_load1, Add):
                            load_args1 = scaled_load1.args
                        else:
                            # when the load equation consists of only a single term
                            load_args1 = (scaled_load1,)
                        load_eq1 = [i.subs(l) for i in load_args1]
                    else:
                        if isinstance(self.load, Add):
                            load_args1 = self.load.args1
                        else:
                            load_args1 = (self.load,)
                        load_eq1 = [i.subs(l) for i in load_args if list(i.atoms(SingularityFunction))[0].args[2] >= 0]
                    load_eq1 = -Add(*load_eq1)-height

                    # filling higher order loads with colour
                    expr = height + load_eq1.rewrite(Piecewise)
                    y1_ = lambdify(x, expr, 'numpy')

                y = numpy.arange(0, float(length), 0.001)
                y2 = float(height)

                if(plus == 1 and minus == 1):
                    fill = {'x': y, 'y1': y1(y), 'y2': y1_(y), 'color':'darkkhaki'}
                elif(plus == 1):
                    fill = {'x': y, 'y1': y1(y), 'y2': y2, 'color':'darkkhaki'}
                else:
                    fill = {'x': y, 'y1': y1_(y), 'y2': y2, 'color':'darkkhaki'}
        return annotations, markers, load_eq, load_eq1, fill


    def _draw_supports(self, length, l):
        height = float(length/10)

        support_markers = []
        support_rectangles = []
        for support in self._applied_supports:
            if l:
                pos =  support[0].subs(l)
            else:
                pos = support[0]

            if support[1] == "pin":
                support_markers.append({'args':[pos, [0]], 'marker':6, 'markersize':13, 'color':"black"})

            elif support[1] == "roller":
                support_markers.append({'args':[pos, [-height/2.5]], 'marker':'o', 'markersize':11, 'color':"black"})

            elif support[1] == "fixed":
                if pos == 0:
                    support_rectangles.append({'xy':(0, -3*height), 'width':-length/20, 'height':6*height + height, 'fill':False, 'hatch':'/////'})
                else:
                    support_rectangles.append({'xy':(length, -3*height), 'width':length/20, 'height': 6*height + height, 'fill':False, 'hatch':'/////'})

        return support_markers, support_rectangles



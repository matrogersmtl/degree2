# -*- coding: utf-8 -*-
'''
A module for construction of vector valued Siegel modular forms.
'''

from __future__ import print_function

from abc import ABCMeta, abstractmethod, abstractproperty
import os
import hashlib
import time

from sage.all import (cached_method, mul, fork, matrix, QQ, gcd, latex,
                      PolynomialRing, ZZ)

from degree2.all import degree2_modular_forms_ring_level1_gens

from degree2.utils import find_linearly_indep_indices

from degree2.scalar_valued_smfs import x5__with_prec

from degree2.rankin_cohen_diff import (vector_valued_rankin_cohen,
                                       rankin_cohen_pair_sym,
                                       rankin_cohen_pair_det2_sym,
                                       rankin_cohen_triple_det_sym,
                                       rankin_cohen_triple_det3_sym)

from degree2.elements import SymWtModFmElt as SWMFE
from degree2.basic_operation import PrecisionDeg2

scalar_wts = [4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16]

gens_latex_name = {4: "\\phi_{4}",
                   6: "\\phi_{6}",
                   5: "\\chi_{5}",
                   10: "\\chi_{10}",
                   12: "\\chi_{12}",
                   35: "\\chi_{35}"}


def _prec_value(prec):
    if prec in ZZ:
        return prec
    elif isinstance(prec, PrecisionDeg2):
        return prec._max_value()
    else:
        raise NotImplementedError


class ScalarModFormConst(object):

    def __init__(self, wts):
        """
        Used for construction of scalar valued Siegel modular forms of
        even weights.
        wts is a list or a dict.

        If wts is a list, elements should be in [4, 5, 6, 10, 12, 35].
        Each integer corresponds to the weight of a generator.
        Then self.calc_form returns a monomial of generators corresponding to
        wts.

        If wts is a dict, its keys should be a tuple each element in
        [4, 5, 6, 12, 35].
        self.calc_form returns a polynomial of generators corresponding to wts.
        """
        if not isinstance(wts, (list, dict)):
            raise TypeError
        self._wts = wts

    @property
    def wts(self):
        return self._wts

    def name(self):
        return "f_{wts}".format(wts="_".join(str(a) for a in self.wts))

    def __eq__(self, other):
        if isinstance(other, ScalarModFormConst):
            return self._frozen_wts() == other._frozen_wts()
        else:
            raise NotImplementedError

    def weight(self):
        return sum(self.wts)

    def __repr__(self):
        return "ScalarModFormConst({a})".format(a=str(self.wts))

    def _frozen_wts(self):
        if isinstance(self.wts, list):
            return tuple(self.wts)
        else:
            return frozenset((k, v) for k, v in self.wts.iteritems())

    @property
    def _key(self):
        return self._frozen_wts()

    def _to_wts_dict(self):
        if isinstance(self.wts, dict):
            return self.wts
        else:
            return {tuple(self.wts): QQ(1)}

    def _chi5_degree(self):
        coeffs_dct = self._to_wts_dict()
        return max([ks.count(5) for ks in coeffs_dct])

    def calc_form(self, prec):
        es4, es6, x10, x12, x35 = degree2_modular_forms_ring_level1_gens(prec)
        x5 = x5__with_prec(prec)
        d = {4: es4, 6: es6, 10: x10, 12: x12, 5: x5, 35: x35}
        return self._calc_from_gens_dict(d)

    def _calc_from_gens_dict(self, dct):
        coeffs_dct = self._to_wts_dict()

        def _monm(ws):
            return mul(dct[k] for k in ws)

        return sum(_monm(k) * v for k, v in coeffs_dct.iteritems())

    def _polynomial_expr(self):
        R = PolynomialRing(QQ,
                           names="phi4, phi6, chi10, chi12, chi35, chi5")
        es4, es6, chi10, chi12, chi35, chi5 = R.gens()
        d = {4: es4, 6: es6, 10: chi10, 12: chi12, 35: chi35, 5: chi5}
        return self._calc_from_gens_dict(d)

    def _latex_(self):
        return latex(self._polynomial_expr())


def latex_expt(n):
    if n == 1:
        return ""
    else:
        return "^{%s}" % str(n)


def latex_rankin_cohen(i, j, lcs):
    if i == 0:
        sub = "\\mathrm{Sym}(%s)" % (j,)
    else:
        sub = "\\det%s \\mathrm{Sym}(%s)" % (latex_expt(i), j)
    l = ", ".join([c for c in lcs])
    return "\\left\\{%s\\right\\}_{%s}" % (l, sub)


scalar_mod_form_wts = {4: [[4]],
                       5: [[5]],
                       6: [[6]],
                       8: [[4, 4]],
                       9: [[4, 5]],
                       10: [[10], [4, 6]],
                       12: [[12], [6, 6], [4, 4, 4]],
                       13: [[4, 4, 5]],
                       14: [[10, 4], [6, 4, 4]],
                       15: [[5, 10], [4, 5, 6]],
                       16: [[4, 12], [6, 10], [4, 6, 6], [4, 4, 4, 4]]}


def _scalar_mod_form_consts():
    return {k: [ScalarModFormConst(a) for a in v] for k, v in
            scalar_mod_form_wts.items()}


scalar_mod_form_consts = _scalar_mod_form_consts()


def rankin_cohen_quadruple_det_sym(j, f1, f2, f3, f4):
    """
    Returns a modular form of wt sym(j) det^(sum + 1).
    """
    return f3 * rankin_cohen_triple_det_sym(j, f1, f2, f4)


def rankin_cohen_quadruple_det_sym_1(j, f1, f2, f3, f4):
    """
    Returns a modular form of wt sym(j) det^(sum + 1).
    """
    F = rankin_cohen_pair_sym(j, f1, f2) * f3
    return vector_valued_rankin_cohen(f4, F)


def rankin_cohen_quadruple_det3_sym(j, f1, f2, f3, f4):
    """
    Returns a modular form of wt sym(j) det^(sum + 3).
    """
    return f3 * rankin_cohen_triple_det3_sym(j, f1, f2, f4)


def rankin_cohen_quadruple_det3_sym_1(j, f1, f2, f3, f4):
    """
    Returns a modular form of wt sym(j) det^(sum + 3).
    """
    F = rankin_cohen_pair_det2_sym(j, f1, f2) * f3
    return vector_valued_rankin_cohen(f4, F)


class ConstVectBase(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def calc_form(self, prec):
        '''Return the corresponding modular form with precision prec.
        '''
        pass

    @abstractmethod
    def _latex_using_dpd_depth1(self, dpd_dct):
        '''dpd_dct is a dictionary whose set of keys is equal to
        self.dependencies_depth1() and its value is a variable name.
        This method returns a LaTeX expression of self.
        '''
        pass

    @abstractmethod
    def weight(self):
        pass

    def _fname(self, data_dir):
        return os.path.join(data_dir, self._unique_name + ".sobj")

    def save_form(self, form, data_dir):
        form.save_as_binary(self._fname(data_dir))

    def load_form(self, data_dir):
        try:
            return SWMFE.load_from(self._fname(data_dir))
        except IOError:
            raise IOError("cache file for %s is not found" % (repr(self), ))

    def calc_form_and_save(self, prec, data_dir, force=False):
        def calc():
            return self.calc_form(prec)
        self._do_and_save(calc, data_dir, force=force)

    def _saved_form_has_suff_prec(self, prec, data_dir):
        '''Return true if the cache file exists and the precision of the
        cached form in data_dir has greater than or equal to given prec.
        '''
        if not os.path.exists(self._fname(data_dir)):
            return False
        f = self.load_form(data_dir)
        return bool(f.prec >= PrecisionDeg2(prec))

    def _do_and_save(self, call_back, data_dir, force=False):
        '''Compute a modular form by call_back save the result to data_dir.
        If force is True, it overwrites the existing file.
        '''
        if force or not os.path.exists(self._fname(data_dir)):
            f = call_back()
            self.save_form(f, data_dir)

    @abstractproperty
    def _key(self):
        pass

    @abstractproperty
    def sym_wt(self):
        pass

    @property
    def _unique_name(self):
        '''
        Returns a unique name by using hashlib.sha1.
        '''
        m = hashlib.sha1()
        m.update(str(self._key))
        return m.hexdigest()

    def __hash__(self):
        return hash(self._key)

    def __eq__(self, other):
        return isinstance(other, ConstVectBase) and self._key == other._key

    @abstractmethod
    def needed_prec_depth1(self, prec):
        '''prec: an integer or an instance of PrecisionDeg2.
        This method should return a non-negative integer.
        To compute self with precision prec, dependencies_depth1 and instances
        of ScalarModFormConst that self depends on have to be
        with precision this value.
        '''
        pass

    @abstractmethod
    def dependencies_depth1(self):
        '''This method should return a list of instances of (child classes of)
        ConstVectBase needed for the computation of self.
        It is not necessary to add dependencies of the dependencies to
        the list.
        '''
        pass

    def walk(self):
        '''Returns a generator that yields all dependencies of self and Self.
        It yields Elements that have less dependencies early.
        '''
        dep_dpth1 = self.dependencies_depth1()
        if not dep_dpth1:
            yield self
        else:
            for c in dep_dpth1:
                for a in c.walk():
                    yield a
            yield self

    @abstractmethod
    def calc_form_from_dependencies_depth_1(self, prec, depds_dct):
        '''depds_dct is a dictionary whose set of keys contains
        dependencies_depth1. And its at an element of dependencies_depth1
        is a modular form with precision prec.
        This method computes a modular form corresponding to self form
        depds_dct.
        '''
        pass


class ConstVectValued(ConstVectBase):

    def __init__(self, sym_wt, consts, inc, tp):
        self._sym_wt = sym_wt
        self._consts = consts
        self._inc = inc
        self._type = tp

    def dependencies_depth1(self):
        return []

    @property
    def sym_wt(self):
        return self._sym_wt

    def weight(self):
        return sum([c.weight() for c in self.consts]) + self.inc

    @property
    def consts(self):
        return self._consts

    @property
    def inc(self):
        return self._inc

    @property
    def type(self):
        return self._type

    def __iter__(self):
        for a in [self.consts, self.inc, self.type]:
            yield a

    def __repr__(self):
        return "ConstVectValued({sym_wt}, {a}, {b}, {c})".format(
            sym_wt=str(self.sym_wt),
            a=str(self.consts),
            b=str(self.inc),
            c="None" if self.type is None else "'%s'" % self.type)

    @property
    def _key(self):
        res = ("ConstVectValued",
               self.sym_wt,
               tuple([a._frozen_wts() for a in self.consts]),
               self.inc, self.type)
        return res

    def needed_prec_depth1(self, prec):
        prec = _prec_value(prec)
        nm_of_x5 = sum(c._chi5_degree() for c in self.consts)
        return prec + nm_of_x5 // 2

    def calc_form_from_dependencies_depth_1(self, prec, depds_dct):
        return self.calc_form(prec)

    def calc_form(self, prec):
        prec = self.needed_prec_depth1(prec)

        funcs = {2: self._calc_form2,
                 3: self._calc_form3,
                 4: self._calc_form4}
        l = len(self.consts)

        if l in [2, 3, 4]:
            return funcs[l](prec)
        else:
            raise NotImplementedError

    def forms(self, prec):
        return [c.calc_form(prec) for c in self.consts]

    def _calc_form2(self, prec):
        funcs = {0: rankin_cohen_pair_sym,
                 2: rankin_cohen_pair_det2_sym}
        func = funcs[self.inc]
        forms = self.forms(prec)
        return func(self.sym_wt, *forms)

    def _calc_form3(self, prec):
        funcs = {1: rankin_cohen_triple_det_sym,
                 3: rankin_cohen_triple_det3_sym}
        func = funcs[self.inc]
        forms = self.forms(prec)
        return func(self.sym_wt, *forms)

    def _calc_form4(self, prec):
        if self.inc == 1:
            funcs = {'a': rankin_cohen_quadruple_det_sym,
                     'b': rankin_cohen_quadruple_det_sym_1}
            func = funcs[self.type]
            forms = self.forms(prec)
            return func(self.sym_wt, *forms)
        elif self.inc == 3:
            funcs = {'a': rankin_cohen_quadruple_det3_sym,
                     'b': rankin_cohen_quadruple_det3_sym_1}
            func = funcs[self.type]
            forms = self.forms(prec)
            return func(self.sym_wt, *forms)
        else:
            raise NotImplementedError

    def _latex_(self):
        if len(self.consts) in [2, 3]:
            return self._latex()
        elif len(self.consts) == 4:
            return self._latex4()
        else:
            raise NotImplementedError

    def _latex_using_dpd_depth1(self, dpd_dct):
        return self._latex()

    def _latex(self):
        lcs = [c._latex_() for c in self.consts]
        return latex_rankin_cohen(self.inc, self.sym_wt, lcs)

    def _latex4(self):
        f1, f2, f3, f4 = self.consts
        if self.type == "a":
            lcs = [c._latex_() for c in [f1, f2, f4]]
            lrc = latex_rankin_cohen(self.inc, self.sym_wt, lcs)
            return "%s %s" % (f3._latex_(), lrc)
        elif self.type == "b":
            lrcp = latex_rankin_cohen(self.inc - 1,
                                      self.sym_wt,
                                      [c._latex_() for c in [f1, f2]])

            lvec = "%s %s" % (f3._latex_(), lrcp)
            lcs = [f4._latex_(), lvec]
            return latex_rankin_cohen(1, self.sym_wt, lcs)


class ConstVectValuedHeckeOp(ConstVectBase):

    def __init__(self, const_vec, m=2):
        self._const_vec = const_vec
        self._m = m
        self._sym_wt = const_vec.sym_wt

    def weight(self):
        return self._const_vec.weight()

    @property
    def sym_wt(self):
        return self._sym_wt

    def __repr__(self):
        return "ConstVectValuedHeckeOp({a}, m={m})".format(
            a=repr(self._const_vec), m=str(self._m))

    @property
    def _key(self):
        return ("ConstVectValuedHeckeOp",
                self._const_vec._key, self._m)

    def dependencies_depth1(self):
        return [self._const_vec]

    def needed_prec_depth1(self, prec):
        prec = _prec_value(prec)
        return self._m * prec

    def calc_form(self, prec):
        f = self._const_vec.calc_form(self._m * prec)
        return self.calc_form_from_f(f, prec)

    def calc_form_from_f(self, f, prec):
        return f.hecke_operator_acted(self._m, prec)

    def calc_form_from_dependencies_depth_1(self, prec, depds_dct):
        f = depds_dct[self._const_vec]
        return self.calc_form_from_f(f, prec)

    def _latex_(self):
        return "\\mathrm{T}(%s) %s" % (self._m, self._const_vec._latex_())

    def _latex_using_dpd_depth1(self, dpd_dct):
        return r"%s \mid \mathrm{T}(%s)" % (dpd_dct[self._const_vec], self._m)


class ConstDivision(ConstVectBase):

    '''Returns a construction for a vector valued modulular form by dividing
    a scalar valued modular form.
    This construction correponds to
    sum(F*a for F, a in zip(consts, coeffs)) / scalar_const.
    Needed prec is increased by inc.
    '''

    def __init__(self, consts, coeffs, scalar_const, inc):
        self._consts = consts
        self._coeffs = coeffs
        self._inc = inc
        self._scalar_const = scalar_const

    @property
    def sym_wt(self):
        return self._consts[0].sym_wt

    @cached_method
    def weight(self):
        return self._consts[0].weight() - self._scalar_const.weight()

    def __repr__(self):
        return "ConstDivision({consts}, {coeffs}, {scc}, {inc})".format(
            consts=str(self._consts),
            coeffs=str(self._coeffs),
            scc=self._scalar_const,
            inc=str(self._inc))

    def dependencies_depth1(self):
        return self._consts

    def needed_prec_depth1(self, prec):
        prec = _prec_value(prec)
        return prec + self._inc

    def calc_form(self, prec):
        forms = [c.calc_form(prec + self._inc) for c in self._consts]
        return self.calc_from_forms(forms, prec)

    @property
    def _key(self):
        return ("ConstDivision",
                tuple([c._key for c in self._consts]),
                tuple([a for a in self._coeffs]),
                self._scalar_const._key, self._inc)

    def calc_from_forms(self, forms, prec):
        f = self._scalar_const.calc_form(prec + self._inc)
        g = sum((a * f for a, f in zip(self._coeffs, forms)))
        return g.divide(f, prec, parallel=True)

    def calc_form_from_dependencies_depth_1(self, prec, depds_dct):
        forms = [depds_dct[c] for c in self._consts]
        return self.calc_from_forms(forms, prec)

    def _latex_using_dpd_depth1(self, dpd_dct):
        names = [dpd_dct[c] for c in self._consts]
        _gcd = QQ(gcd(self._coeffs))
        coeffs = [c / _gcd for c in self._coeffs]
        coeffs_names = [(c, n) for c, n in zip(coeffs, names)
                        if c != 0]
        tail_terms = ["%s %s %s" % ("+" if c > 0 else "", c, n)
                      for c, n in coeffs_names[1:]]
        c0, n0 = coeffs_names[0]
        head_term = str(c0) + " " + str(n0)
        return r"\frac{{{pol_num}}}{{{pol_dnm}}} \left({terms}\right)".format(
            pol_dnm=latex(_gcd.denominator() *
                          self._scalar_const._polynomial_expr()),
            pol_num=latex(_gcd.numerator()),
            terms=" ".join([head_term] + tail_terms))


class ConstDivision0(ConstDivision):

    '''
    This class is obsolete. Use ConstDivision instead.
    '''

    def __init__(self, consts, coeffs, scalar_const):
        ConstDivision.__init__(self, consts, coeffs, scalar_const, 0)

    def __repr__(self):
        return "ConstDivision0({consts}, {coeffs}, {scc})".format(
            consts=str(self._consts),
            coeffs=str(self._coeffs),
            scc=str(self._scalar_const))

    @property
    def _key(self):
        return ("ConstDivision0",
                tuple([c._key for c in self._consts]),
                tuple([a for a in self._coeffs]),
                self._scalar_const._key)


class ConstMul(ConstVectBase):

    def __init__(self, const, scalar_const):
        self._const_vec = const
        self._scalar_const = scalar_const

    @property
    def sym_wt(self):
        return self._const_vec[0].sym_wt

    def weight(self):
        return self._const_vec.weight() + self._scalar_const.weight()

    def __repr__(self):
        return "ConstMul({const}, {scc})".format(
            const=str(self._const_vec),
            scc=self._scalar_const)

    @property
    def _key(self):
        return ("ConstMul", self._const_vec._key, self._scalar_const._key)

    def calc_form(self, prec):
        f = self._const_vec.calc_form(prec)
        return self.calc_form_from_f(f, prec)

    def dependencies_depth1(self):
        return [self._const_vec]

    def needed_prec_depth1(self, prec):
        if self._scalar_const._chi5_degree() > 0:
            raise NotImplementedError
        return _prec_value(prec)

    def calc_form_from_f(self, f, prec):
        g = self._scalar_const.calc_form(self.needed_prec_depth1(prec))
        return f * g

    def calc_form_from_dependencies_depth_1(self, prec, depds_dct):
        f = depds_dct[self._const_vec]
        return self.calc_form_from_f(f, prec)

    def _latex_using_dpd_depth1(self, dpd_dct):
        return "%s %s" % (self._scalar_const._latex_(),
                          dpd_dct[self._const_vec])


def dependencies(vec_const):
    '''Returns a set of instances of ConstVectBase needed for the computation
    of vec_const.
    '''
    dep_dpth1 = vec_const.dependencies_depth1()
    if not dep_dpth1:
        # No dependencies.
        return set([])
    else:
        return reduce(lambda x, y: x.union(y),
                      (dependencies(c) for c in dep_dpth1),
                      set(dep_dpth1))


def needed_precs(vec_const, prec):
    '''Returns a dict whose set of keys is equal to the union of
    dependencies(vec_const) and set([vec_const])
    and whose values are equal to needed_prec_depth1.
    '''
    prec = _prec_value(prec)
    dep_dpth1 = vec_const.dependencies_depth1()
    res = {}
    nprec = vec_const.needed_prec_depth1(prec)
    res[vec_const] = nprec
    dcts = [needed_precs(c, nprec) for c in dep_dpth1]
    for c in dependencies(vec_const):
        res[c] = max(d.get(c, prec) for d in dcts)
    return res


class CalculatorVectValued(object):

    def __init__(self, const_vecs, data_dir):
        self._const_vecs = const_vecs
        self._data_dir = data_dir

    def file_name(self, c):
        return c._fname(self._data_dir)

    def _mat_ls(self, consts, prec):
        prec = PrecisionDeg2(prec)
        sym_wt = consts[0].sym_wt
        d = self.forms_dict(prec)
        ts = [(t, i) for t in prec for i in range(sym_wt + 1)]
        return [[d[c][t] for t in ts] for c in consts]

    def rank(self, consts, prec=5):
        return matrix(self._mat_ls(consts, prec)).rank()

    def linearly_indep_consts(self, consts, prec=5):
        ms = self._mat_ls(consts, prec)
        idcs = find_linearly_indep_indices(ms, matrix(ms).rank())
        return [consts[i] for i in idcs]

    def all_dependencies(self):
        '''Returns a set of all dependencies needed for the computation.
        '''
        return reduce(lambda x, y: x.union(y),
                      (dependencies(c) for c in self._const_vecs))

    @cached_method
    def all_needed_precs(self, prec):
        '''Returns a dict whose set of keys is equal to the union of
        all_dependencies and set(self._const_vecs) and whose values are
        equal to needed_prec.
        '''
        prec = _prec_value(prec)
        res = {}
        dcts = [needed_precs(c, prec) for c in self._const_vecs]
        kys = self.all_dependencies().union(set(self._const_vecs))
        for c in kys:
            res[c] = max(d.get(c, prec) for d in dcts)
        return res

    def rdeps(self, const):
        '''Returns a subset of the union of all_dependencies and
        set(self._const_vecs) cosisting elements
        that depend on const with depth1.
        '''
        return {c for c in self.all_dependencies().union(set(self._const_vecs))
                if const in c.dependencies_depth1()}

    def rdep_prec(self, const, prec):
        '''We have to compute const with this precision to compute self._consts
        with precision prec.
        '''
        d = self.all_needed_precs(prec)
        _rdeps = self.rdeps(const)
        if _rdeps:
            return max(d[a] for a in _rdeps)
        else:
            return _prec_value(prec)

    def calc_forms_and_save(self, prec, verbose=False, do_fork=False,
                            force=False):
        '''Compute self._const_vecs and save the result to self._data_dir.
        If verbose is True, then it shows a message when each computation is
        done.
        If force is True, then it overwrites existing files.
        If do_fork is True, fork the process in each computation.
        '''
        if not os.path.exists(self._data_dir):
            raise IOError("%s does not exist." % (self._data_dir,))

        def msg(c, prc):
            return "{t}: Computing {c} with prec {prc}".format(
                c=repr(c),
                t=str(time.ctime()),
                prc=str(prc))

        if verbose:
            print("Start: " + time.ctime())

        computed_consts = []

        def calc_and_save(c, prc):
            def call_back():
                depds_dct = {dp: dp.load_form(self._data_dir)
                             for dp in c.dependencies_depth1()}
                f = c.calc_form_from_dependencies_depth_1(prc, depds_dct)
                return f

            c._do_and_save(call_back, self._data_dir, force=force)

        if do_fork:
            calc_and_save = fork(calc_and_save)

        for c in self._const_vecs:
            for b in c.walk():
                if b not in computed_consts:
                    prc = self.rdep_prec(b, prec)
                    if verbose:
                        print(msg(b, prc))
                    if not b._saved_form_has_suff_prec(prc, self._data_dir):
                        calc_and_save(b, self.rdep_prec(b, prec))
                    computed_consts.append(b)

        if verbose:
            print("Finished: " + time.ctime())

    def forms_dict(self, prec):
        return {c: (c.load_form(self._data_dir))._down_prec(prec)
                for c in self._const_vecs}

    def unique_names_dict(self):
        return {c: c._unique_name for c in self._const_vecs}


def check_collision(consts):
    keys = [a._key for a in consts]
    names = [a._unique_name for a in consts]
    assert len(keys) == len(names)

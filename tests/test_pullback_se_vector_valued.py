# -*- coding: utf-8 -*-
import unittest
from degree2.diff_operator_pullback_vector_valued import (
    bracket_power, ad_bracket, _Z_U_ring, _diff_z_exp,
    fc_of_pullback_of_diff_eisen, _U_ring, sqcap_mul, D_tilde_nu,
    algebraic_part_of_standard_l, _pullback_vector, _u3_u4_nonzero)
from sage.all import (random_matrix, QQ, binomial, identity_matrix, exp,
                      random_vector, symbolic_expression, ZZ, derivative,
                      block_matrix, matrix, cached_function)
from degree2.vector_valued_smfs import vector_valued_siegel_modular_forms as vvsmf
from degree2.scalar_valued_smfs import x12_with_prec, x35_with_prec
from unittest import skip
from ..siegel_series.tests.utils import random_even_symm_mat
from degree2.all import CuspFormsDegree2
from degree2.standard_l_scalar_valued import tpl_to_half_int_mat, G_poly


@cached_function
def _wt10_13_space_forms():
    M = vvsmf(10, 13, prec=4)
    f = M.eigenform_with_eigenvalue_t2(QQ(84480))
    g = M.eigenform_with_eigenvalue_t2(QQ(-52800))
    return (M, f, g)


class TestPullBackVectorValued(unittest.TestCase):

    @skip("OK")
    def test_bracket_power_ad_bracket(self):
        for n in range(2, 6):
            for _ in range(1000):
                m = random_matrix(QQ, n)
                self.assertEqual(bracket_power(m, n)[0, 0], m.det())
                for p in range(n + 1):
                    self.assertEqual(ad_bracket(m, p) * bracket_power(m, p),
                                     m.det() * identity_matrix(QQ, binomial(n, p)))

    @skip("OK")
    def test_diff_z_exp(self):
        z11 = symbolic_expression("z11")
        for _ in range(500):
            n = random_vector(QQ, 1)[0]
            m = random_vector(ZZ, 1)[0].abs()
            r_pol = sum(a * b for a, b in
                        zip(random_vector(QQ, 5), (z11 ** a for a in range(5))))
            pol_exp = r_pol * exp(n * z11)
            r_pol_diff_se = (
                derivative(pol_exp, z11, m) / exp(n * z11)).canonicalize_radical()
            r_pol_diff_se = _Z_U_ring(r_pol_diff_se)
            r_pol_diff = _diff_z_exp(
                (m, 0, 0, 0), _Z_U_ring(r_pol), [n, 0, 0, 0], base_ring=_Z_U_ring)
            self.assertEqual(r_pol_diff, r_pol_diff_se)

    @skip("ok")
    def test_pullback_diff_eisen_sym2_wt14(self):
        M = vvsmf(2, 14, 5)
        u1, _ = _U_ring.gens()
        # cusp form
        f = M.eigenform_with_eigenvalue_t2(QQ(-19200))
        f = f * f[(1, 1, 1), 0] ** (-1)
        A = tpl_to_half_int_mat((1, 1, 1))
        D = A

        def fc_pb(a):
            return fc_of_pullback_of_diff_eisen(12, 14, 2, a, D, 1, 1)

        fc_111 = fc_pb(A)
        a0 = fc_111[u1 ** 2]

        def assert_eq(t):
            a = tpl_to_half_int_mat(t)
            self.assertEqual(f[t]._to_pol(), fc_pb(a) / a0)

        assert_eq((1, 1, 1))
        assert_eq((2, 1, 3))
        assert_eq((2, 0, 3))

    @skip("ok")
    def test_pullback_diff_eisen_scalar_wt12(self):
        x12 = x12_with_prec(5)
        self.assert_pullback_scalar_valued(x12, (1, 1, 1),
                                           [(2, 1, 3), (2, 0, 2), (2, 2, 3)], 10)

    @skip("ok")
    def test_pullback_diff_eisen_scalar_wt12_diff4(self):
        x12 = x12_with_prec(5)
        self.assert_pullback_scalar_valued(x12, (1, 1, 1),
                                           [(2, 1, 3), (2, 0, 2), (2, 2, 3)], 8, verbose=True)

    @skip("ok")
    def test_pullback_diff_eisen_scalar_wt35(self):
        x35 = x35_with_prec(10)
        self.assert_pullback_scalar_valued(x35, (2, 1, 3),
                                           [(2, -1, 4), (3, -1, 4),
                                            (3, -2, 4)], 34,
                                           verbose=True)

    def assert_pullback_scalar_valued(self, f, t0, ts, l, verbose=False):
        D = tpl_to_half_int_mat(t0)
        f = f * f[t0] ** (-1)
        if verbose:
            print "Compute for %s" % (t0,)
        a = fc_of_pullback_of_diff_eisen(
            l, f.wt, 0, D, D, 1, 1, verbose=verbose)
        self.assertNotEqual(a, 0)
        for t in ts:
            if verbose:
                print "Checking for %s" % (t, )
            A = tpl_to_half_int_mat(t)
            self.assertEqual(fc_of_pullback_of_diff_eisen(l, f.wt, 0, A, D, 1, 1, verbose=verbose),
                             a * f[t])

    @skip("Not ok")
    def test_14_identity(self):
        '''Test idenitity (14) in [Bö].
        '''
        n = 2
        for _ in range(50):
            t1, t2, t3, t4 = random_t1234(n)
            z2 = random_matrix(QQ, n)
            for al in range(n + 1):
                for be in range(n + 1):
                    if al + be <= n:
                        p = n - al - be
                        lhs = sqcap_mul(bracket_power(z2 * t4, al),
                                        sqcap_mul(identity_matrix(QQ, binomial(n, p)),
                                                  bracket_power(z2 * t3, be), n, p, be) *
                                        ad_bracket(t1, p + be) *
                                        bracket_power(t2, p + be),
                                        n, al, p + be)
                        lhs = lhs[0, 0] * QQ(2) ** (-p - 2 * be)
                        rhs = delta_al_be(t1, t2, t4, z2, al, be)
                        self.assertEqual(lhs, rhs)

    @skip("OK")
    def test_delta_p_q_expand(self):
        n = 3
        for _ in range(50):
            t1, t2, t3, t4 = random_t1234(n)
            z2 = random_matrix(QQ, n)
            for q in range(n + 1):
                p = n - q
                lhs = sum(delta_al_be(t1, t2, t4, z2, q - be, be) *
                          (-1) ** be * binomial(q, be) for be in range(q + 1))
                rhs = sqcap_mul(bracket_power(t1 * z2, q) *
                                bracket_power(
                                    t4 - QQ(1) / QQ(4) * t3 * t1 ** (-1) * t2, q),
                                bracket_power(t2, p), n, q, p)
                rhs = rhs[0, 0] * QQ(2) ** (-p)
                self.assertEqual(lhs, rhs)

    @skip("ok")
    def test_diff_pol_value(self):
        for _ in range(50):
            t1, t2, _, t4 = random_t1234(2)
            for k, nu in [(10, 2), (10, 4), (12, 6)]:
                self.assertEqual(scalar_valued_diff_pol_1(k, nu, t1, t4, t2),
                                 scalar_valued_diff_pol_2(k, nu, t1, t4, t2))

    @skip("OK")
    def test_pullback_lin_comb(self):
        M, f, g = _wt10_13_space_forms()
        t0 = f._none_zero_tpl()
        D = tpl_to_half_int_mat(t0)
        u3_val, u4_val, f_t0_pol_val = _u3_u4_nonzero(f, t0)
        vec = _pullback_vector(ZZ(6), D, u3_val, u4_val, M) / f_t0_pol_val
        a = algebraic_part_of_standard_l(f, ZZ(4), M)
        f_vec = M._to_vector(f)
        g_vec = M._to_vector(g)
        m = (matrix([f_vec, g_vec]).transpose()) ** (-1)
        self.assertEqual((m * vec)[0], a)

    @skip("ok")
    def test_pullback_lin_comb1(self):
        M, f, _ = _wt10_13_space_forms()
        self.assert_pullback_lin_comb(
            M, f, 6, [(1, 1, 2), (2, 1, 2)], verbose=True)

    def assert_pullback_lin_comb(self, M, f, l, ts, verbose=False):
        j = f.sym_wt
        k = f.wt
        t0 = f._none_zero_tpl()
        D = tpl_to_half_int_mat(t0)
        u3_val, u4_val, _ = _u3_u4_nonzero(f, t0)
        vec = _pullback_vector(l, D, u3_val, u4_val, M)
        f_vec = M._to_form(vec)

        for t in ts:
            A = tpl_to_half_int_mat(t)
            fc = fc_of_pullback_of_diff_eisen(l, k, j, A, D, u3_val, u4_val)
            if verbose:
                print "Checking for t = %s" % (t, )
            if j > 0:
                self.assertEqual(fc, f_vec[t]._to_pol())
            else:
                self.assertEqual(fc, f_vec[t])

    @skip("OK")
    def test_pullback_lin_comb_wt14_scalar(self):
        S14 = CuspFormsDegree2(14, prec=4)
        f = S14.basis()[0]
        self.assert_pullback_lin_comb(S14, f, 6, [(1, 1, 2), (2, 1, 2)])

    @skip("OK")
    def test_pullback_linear_comb2(self):
        M, f, g = _wt10_13_space_forms()
        a = algebraic_part_of_standard_l(f, 10, M)
        b = algebraic_part_of_standard_l(g, 10, M)
        t0 = f._none_zero_tpl()
        u3_val, u4_val, _ = _u3_u4_nonzero(f, t0)
        u3, u4 = f[t0]._to_pol().parent().gens()
        af = f[t0]._to_pol().subs({u3: u3_val, u4: u4_val})
        ag = g[t0]._to_pol().subs({u3: u3_val, u4: u4_val})
        A = tpl_to_half_int_mat(t0)
        self.assertEqual((f[t0] * af * a + g[t0] * ag * b)._to_pol(),
                         fc_of_pullback_of_diff_eisen(12, 13, 10, A, A, u3_val, u4_val))


def delta_al_be(t1, t2, t4, z2, al, be):
    n = z2.ncols()
    p = n - al - be
    t3 = t2.transpose()
    res = sqcap_mul(bracket_power(t1 * z2, al + be) *
                    sqcap_mul(bracket_power(t4, al),
                              bracket_power(t3 * t1 ** (-1) * t2, be), n, al, be),
                    bracket_power(t2, p), n, al + be, p)
    res = res[0, 0] * (QQ(2) ** (- p - 2 * be))
    return res


def random_t1234(n):
    t2 = random_matrix(QQ, n)
    t3 = t2.transpose()
    t1 = random_even_symm_mat(n).change_ring(QQ)
    t4 = random_even_symm_mat(n).change_ring(QQ)
    return [t1, t2, t3, t4]


def scalar_valued_diff_pol_1(k, nu, A, D, R):
    mat = block_matrix([[A, R / ZZ(2)], [R.transpose() / ZZ(2), D]])
    G = G_poly(k, nu)
    y1, y2, y3 = G.parent().gens()
    G_y1_y3 = G.subs({y2: A.det() * D.det()})
    return G_y1_y3.subs({y1: R.det() / ZZ(4), y3: mat.det()}).constant_coefficient()


def scalar_valued_diff_pol_2(k, nu, A, D, R):
    A0 = D0 = tpl_to_half_int_mat((1, 1, 1))
    a0 = QQ(
        D_tilde_nu(k, nu, QQ(1), [ZZ(0)] * 4, A=A0, D=D0).constant_coefficient())
    b0 = QQ(scalar_valued_diff_pol_1(
        k, nu, A0, D0, tpl_to_half_int_mat((0, 0, 0))))
    a = b0 / a0
    return QQ(D_tilde_nu(k, nu, QQ(1), R.list(), A=A, D=D).constant_coefficient()) * a

suite = unittest.TestLoader().loadTestsFromTestCase(TestPullBackVectorValued)
unittest.TextTestRunner(verbosity=2).run(suite)

import unittest
import numpy as np
from calibrate import estimates, corrected_slope, design


class QualificationChecks(unittest.TestCase):
    def test_ols_partial_regression_matches_independent_projection(self):
        rng=np.random.default_rng(42)
        ind,_,w=design(6)
        x=rng.uniform(.2,.8,len(ind)); y=rng.normal(size=len(ind))
        b,methods=estimates(w,x,y,ind)
        xr=x-w@np.linalg.lstsq(w,x,rcond=None)[0]
        yr=y-w@np.linalg.lstsq(w,y,rcond=None)[0]
        beta=xr@yr/(xr@xr)
        residual=yr-beta*xr
        expected_se=np.sqrt(residual@residual/(len(x)-w.shape[1]-1)/(xr@xr))
        self.assertAlmostEqual(b[-1],beta)
        self.assertAlmostEqual(methods['OLS'][0][-1],expected_se)
        self.assertEqual(methods['OLS'][1],9)

    def test_hc3_matches_explicit_leave_one_out_changes(self):
        rng=np.random.default_rng(72)
        ind,_,w=design(6); x=rng.uniform(.2,.8,len(ind)); y=rng.normal(size=len(ind))
        a=np.column_stack([w,x-.55]); b,methods=estimates(w,x,y,ind)
        changes=[]
        for i in range(len(x)):
            mask=np.arange(len(x))!=i
            changes.append(np.linalg.lstsq(a[mask],y[mask],rcond=None)[0]-b)
        np.testing.assert_allclose(methods['HC3'][0],np.sqrt(np.square(changes).sum(axis=0)),rtol=1e-9)

    def test_correction_equals_ols_without_measurement_error(self):
        rng=np.random.default_rng(9); ind,_,w=design(6)
        x=rng.uniform(.2,.8,len(ind)); y=rng.normal(size=len(ind))
        b,_=estimates(w,x,y,ind)
        self.assertAlmostEqual(corrected_slope(w,x,y,np.zeros(len(x))),b[-1])

    def test_unidentified_correction_returns_missing_not_zero(self):
        ind,_,w=design(6); x=np.ones(len(ind))*.5
        self.assertIsNone(corrected_slope(w,x,np.arange(len(x)),np.ones(len(x))))


if __name__=='__main__':unittest.main()

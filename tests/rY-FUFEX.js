import {N as a} from "./DNmjgBLm.js";

const aaa = (x,y) => {
    const ret=a(x,y);
    ret.then((r)=>{window.__hook(x,y,r)});
    return ret;
};

const t = n => aaa("/sun/ranking/fundRankV3", {
    data: n
})
  , o = n => a("/pub/pubRanking/newFundV3", {
    data: n
})
  , c = n => a("/sun/manager/collections", {
    data: n
})
  , e = n => a("/sun/company/collections", {
    data: n
})
  , i = () => a("/sun/company/collectionItems", {})
  , r = () => a("/sun/chart/barometer", {})
  , u = n => a("/sun/Ranking/hotSearchApi", {
    data: n
})
  , m = n => a("/sun/ranking/cityList", {
    data: {
        pid: n
    }
})
  , p = () => a("/sun/ranking/provinceList", {})
  , g = n => a("/sun/chart/marketLine", {
    data: n
});
export {e as a, m as b, i as c, g as d, r as e, t as f, p as g, u as h, c as m, o as p};

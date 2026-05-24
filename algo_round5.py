import base64
import json
import zlib

try:
    from datamodel import ProsperityEncoder, TradingState
except ImportError:
    from prosperity4bt.datamodel import ProsperityEncoder, TradingState

_PACKED=(
    'c-rkf{a53*vj2)7KP8aRK$m;(%ORX&f){c(Bxw@Z-4}9v3^Cwt5~s04ySI1$_ova9^<~FlfkM~qIW4h9qtR$2jYc!0Kew)z-u&j?kGAU8pIbNKJc^gAn>YyP=);z`io>NJ`OBO8pQN&iwKWN6eiR2c'
    'DjffgVD7xB_s3Tif__Ei0Yd4`V-<jXMiA5Bw^cAv0q9p$9xm^^xlRQ8j35@vF!lqjJM1$+td_xTaO0VJEtMhI)q@IwzM$_9{u1@so2sS!`!_<$1ToOa>(N%v?l^6C@6$fuV?W*{Kla6veX-;n`Z1P='
    'WVF@q9(RZCNo#QC3;>k;ZuPsJR_8SN(6%o+C;iXKhx2Z)CqZ1=&5Mh3_%s%WbhLG9x9v}#-9Z;&7`Vr6yZOOA>$XXAa^Z>H|KOh6!=cmH3wv$Ui=o~B?DkPBhT4N}+wQyX+xEGWTKcht{>Bt0LN(eN'
    '_U+D~Z4bMB*B%V}T|y<`5K5e8yVV;wZu89UH@kLQDL(Dny|dQPanD<Wp;9*J*-Zx^J}U*6-PQ?e?83n$aVZ{cbw7PRbvo|g%>Do^cAJR$p#!z066ex^adMCQjy*inicjr+yVcY_qfr{_AG>`K)mWM}'
    'qpkB+v)^r=wR&!|)o->jDap6)CE-W%rSCL{cIQ+D9Q<-&_mywMev3ekrFl5o8g$So^gv!D4kVv@h}Aa2(Um{<?LqI@=@W5HKBJMfKN`MY+MQOrZIkBZNsgwQb9{_s)y3UoKhDJ;1M$Zv3GNdSHM|;('
    'wk|H+%hmv7?EIJrIRA2Pqk$OO(zh-WlT%0f)OSv#-=Cd!yZaHhA*?Kjac#%xxxMa*+w2a9-45<A|Ar>WvHP*xZOflKpW7;AuiO6Y4Cri3J`XOO6Es?|Rz=}zd6Tj&1hYlBjICdzaDIjUjhA2RS91&f'
    'bGr;@*2IgwSvc{h7KQ6BC;qZx^_F3@@RvdS)tTRf_|tIdO@jH|AogPaYVQAW<1b>Xg=;y>Ww;d4E_n5K*YWP78-agsrd||T?eOl-XH87}Tg!EWc@Vp9De|YcWvhB*b;7w%0pK6_zB>)?BCBCtZJ~eV'
    'l9~61i%Q+8KfjCb5zNp3Jg7l?tbxTcn8z4<#o7+9fA!H`P(gJUjjJt$uwwc13HtL2)!E8!f2RS}c7F|nd1>Y?N@#d07R6XDTRVVBZ25M&itcI45ikNl1H(}BXmF8;MQCWzj~MaFU%J3u69Ly=<R{%j'
    'f0U9kPGB6mAQ?&#{4>%&@me?GY=Jh-$i?K9D3QSBawShS(w!3dUs@HhuVx5naI>PZ{HdJ$6#fL!2x5PhFt211nX1U)vh~wX*3StJB0bN=a5E%^CPP7*TCV0de0+9^xSSwqsi<8nn-RX~V9F#5vaM5_'
    '3j?2jx$5T<41GySCapRp#MvuORAGWH{dl#UtK&`wD*)}#n=KStMZOrMi&HTTkZw7@i|E+1pXJO-cnIAITG#JcMe$R1WlR~b_WPWE*r3wPTYmB5w0an15k>)QY}wtoM(X?nRvtJ#!Y2{)*f@j<^YAEg'
    '<{8FrG~JE9&aT5L0^6lW2KaO0&%;?T$1RSn+i+>2&2P?8?LK(Z73z4|On^KPm<VYgbVB}&kj4>CcCS}oUA9@EpQ!GX{w7r5&p?TYZx<#9BIcWs7&b<j3_3V#rFax`zQl+x!3|7<-QQM7*GJnu{EaAu'
    '4L`;-lE1jnE3**@_m)c_o3zi_r^Ceng@D(Mu`DEn#iEc1JxtavsTNuU{*>FN<6k!|<*4TFbuj5+R+x*u=u1{H>iRqa_36FuM=3D=9{@1)kotU^0zy=<Ops`G=Pk2HiB|JzaCaZK<`e%91;#LTd|sfs'
    'SoQ=i?k3#ril3=SCdj_&A}8TlOub-!334Igsiciw#>A7RoO#xVT)IOh-65Cmu_&+v2^Uyg6jB+LXkdx~X&b{Eng)>F$!fNUN*Dz7ZyGfWiZs$Vy`>k2%cxNTRcH(JvpQ1H%2K1^Zb@4u`z75f1q!BN'
    '#kvoW)YlLMQe{D-BxFi8k_zD})^zXR?}Mq2P+5l!gsd*h$}E_GvV}@_P$5>S_GO40Z$1go=I0|g-1exBDk&lt++uB4Qnz?Tq;R9A6ME|g3CDEv8ae<Xuz`u)vG(Lre;WA)jF@dup(<9OLyDRsC!Hxi'
    ';~+?K*eR9C=VrHq&de9hVXND5d;RVS`g4#hK39n?imSX=i4{uww)g3s0Z#w+j()?N0y?vwI42pcKUqt??x2Nx+HRe<hNz)EbSfJRyFItv9Sq##&x{D228^eU#1o@BZ*|=6$Bv6hM-`p--M-@jCP0eh'
    's@1tfr~PjKvpe|Ue00w*+QU|_-E#UM;=B6?sMpxIb8_mq!&dVH^cs!cFBjdR{<U>}Y`5)B({bP1t-d=rYrO{w_jeKX{nh~NX&w7ClZ65sdiG$@x^$kO-yiLE+dXe(k1U5yI+-Pgj~Mi;IV?ukX!Cc`'
    '9_gZuu!J=ew)~(OJr83Ge-l(3w73f21zks9H{ont!T%*i^fOuqN-EYeS>80HWr5N#{Nl#JjY1~g2|zE1&<^WQ&<Ygm*scFs$#)SwT{-W(1)vx$VS_~r#?-%!i2{lKs95AP+CTmiEJ~!o3T=3_S09&w'
    'R|Mt=*BHzFMID0%Fc@wLRxA);*0tX~L=jr5o?`&WN8G|SUg}NkXFGqz`r?0WOugCl#IxXA9shT<H!hEAV*wSC773L=Mh32`hKv$g;`Hrs{AeqJorv)$LORsc*SUl$RV+e|L6$iu0e28#jsOFp0{xlA'
    'Hbx$yOeYG<WH7t-rr!L<e|ExZ9JBinPFFM7k+q?`LxPUmuF*yi$^^Wsj~7%xFiC|tjJ+w4owTzfVBw?_IJC3ZQb`pU$WT=URKQM*C1L69)Qe+(&b30S@?o;kq@!oi4VlcUq4`;}kdDE)4)e&&>Jc`V'
    '^5$_nRo?no$9zaJ(*ewl8FOC4%wWd}V^#}LjND~_xJT?A#889(X8gGEBCwr72^!-V)$>-<7%8Jr0Q%^k-`F6-q0YStSMxYB)(`=tnm~cE1{82eYM6%OFYYNUpT<pDJoF(VMU;$3wcVPa;);YBp#@kV'
    '$prJ~)m9XTi-kV{?d83P7Gx9A?CcH1t40>K&I$A*d7zzz;m^@wdeV)9`ASfE@sS$ZNDkjh9d_zL!+^{AF-TL&Nijb6TMalE3@(n(TS(LCcHn5DY0WSMBhrbnRb}Y$UT1Av=4RAE;q`YKx~|S?A|{B<'
    'iQ0J*q8=ljcu@gOL$lK1HIyJKOX5JP=nJ}e;K^A`+vy~Xvt++mi;pi(4aJlv&@0cE#e9m7VQ3yoAZP-jJ%Hoe1~LR2Ee3Px!m#0-Q-zhyY?(yss9~j_F6ye?GF-URFoK26bc~U3SAVY6YGrNW04EL`'
    '2`YnF3f&$FeH)`zhs%|pEZqxl?jr?{m|ADv7yl`?wOcQMbE~2|3TqIOX#J>xRnHU&%hX2TCvGxTI~j4)3TWv-x}vd@!f3JdJ&<!iUWFEU>j~ldsYhrJld;n<YhOq<ar4`j>3B%li?pR1Z$UNKTE$Wh'
    'z|~|xD9xZQW!2bGYfxRiA#mlEFw`aM7VIeG#G;={<Sm6!3yPK{;W#3!sInd_XJ<uZuMywBB%g#m1WqWrVmRUrjVp`@dA@QKN0JJd^ncewQ(`_TX)2FP4R{PgS($*W&u9lqmiL5>Fdxip6m9WKAB>QG'
    '116)oO|t=IOieHzQu%rcrm8fJcr)V)r{PI>$`PXlEsd$X(*~{v^9O$(hs&>S^u_-jtTD-~BokJqM}sf%&EY3ya=?_NIMAd_GXT+vhLHIam#%G8y5+XG9H2rvWDN_u4J37G$A4ReNMokQUNju!7)Qrd'
    'wJB8uj8gsNtV>p`9QA1{$-0_Qa@0uB)<wag02QfKwh{1QQZ-D~YNapBL}~;CY;MT|nk8HUacmt(y2hnyQ+(v)!)F0kzcsp<Kgtl_!wUW=%hg=G^sP&tEaHrZvkKxSHsnu3ZxU(O^JL>xK9b$?PvI6M'
    '`w%AbK0>MwSnBxwo_eyNs^Q$EPU=Ss<KQb6Vw2{q>4cBd3)OQUz)1%_spg;GbbShIg`^tSl**=y0Jd@FGz8?j3*boeYhqdlG$Wfl*8F_YP-dLsiIFU=ifaLrPjb;j#VX@MDY+Pdi;G?Az(kxM2uT^P'
    'OWG>2uEv$-()>6dx2Jb#)4kVDy64USt;sHN&o$Z26~|q{QZD)UYTt>su=bhy2y5S|GjU>cx0}PXJBFuez<8B&ZudVps8gWHd{@)o=>1Hyj}BDeGK;srTqsf1e_xz~ckHFphm*cLJnK7yvu^t&y<Xk='
    '=RsPJX&J(M3I4IIHX@|c#>c^w8!Hue^&L9-rK7Lzkz%+TdK}_!_!6(x22O2I{UDR9Jp<KzjOy0D-ZY$>dyf4fvv~o<0Y^b}oI&gVoJ@MNsNu9UKgc(6C3dumOKE~Zmnm|2V;BReJdM)`sQhN{yI$dS'
    'M{x!Bqh7%+!|O1988g;P8l?UjYmj8_%Ggxv^66n?1JY(jB!haZSU8@-bhO^o@dPHMHD;uzF(qwiPI?r3H#H)CKX>yOlhzrOQq8<CVQAXen3QfQs%W;QwZ<X6%Cp&nNLdv82aI5ewkDm%6(&869SAdt'
    'AgBmbl%LKp1T8QWS`(?3BGH9_3Cg-{%H$xRPP(=C_@<d!&gnCdLyu5fGj03je2xUf(iDeo>@7t(QMiMS|G1oSiTt9%UX_K4bYJ~O>zA3qZi<Z@6i>3Na=s9VqbFwy#w+ljv~&2xBQ3RJVEeDD*}^6J'
    'NQO*;QtLki;VJ@c2pXG+Vk(r0dXV{2SReuq;Qi8%?!zgpacL(mX2l{kX5oX+ooL0jIYAiWC_$ZKe$FFp)wFdAw{d7ypP~_C8|ltAa1ri;Ey_*&J~(pfVehhV!6f`fcE*w5s0oz0<1ibm<nkf-n24Pj'
    'jmvf8O;ef+$cFA8nA{vLADjDdV9aa$HY6^M7>CBx8{w5*1H6oRUojRwvw2@WkSO*VL)*kzMX^%oVA8mX*9WPW1;RbcCi71Vf-}(~ET86yi6kt>E8Lc$zQm%mCA4l1l-zvvHMBmH-4^lwrS1s^&qD(y'
    '?>Z{!>v}n5EjRt6PS}SKsa?U;7ad^McOj(_xMi3jyyzT)J(9B5&<xikrS+^RUOuu0OJjO97y_BvLlc7Rp)F_dTIKU3h`j5m>}d2oz0I<oXLs8)D2Wu5H{)3r886Sg1v->d(F3j0)Kdn6(-MfCDXYIz'
    'novkf@BwN3*LRI=noWGoxU$Y4Sy^`onY+ol;pS~rQ;B@pQO~_JsmPNZV@z~qy&CL!!u_y>!AOZo-jYtFbzQzO7p~CP9)we+Oh%c(a_tgau9=#kz@Wb5-f8nJLMbF`<SM7Lb(1U4xh+L*AI}P^7MgBz'
    '>ziQJI-lRL|58p38+j!pNz|^$zw>^$LZWeCo#GN}06!zp5SOvP+{M9__h_cyLR@SB-u*~Yp?}_V`qheV!i7Jv;t;7qK7v7~PZ>|&zrj+?WG_M(Td_4;MQD8P=Hb$}K#;zo0h?E8RSJqd`Vm$};A$RV'
    '!!ppc#nM|8*@KGgK}GhUB70DgJ*dbYRAdh-vIiB}gNp1yMfRW~dr*-*=#69#qUo1Se$lB}p9R0`)U?s5FiL{xR5&3M^conFOImPTKe2oGHVVg5uJ4(NB7*4jwC|9ZB^;fKz1|+ds&sGn>>NV}SM&dK'
    '`dwFnT2DZpamX{Cj~y%A;dU4DRJZKGBM2_C{uD09Z_VZS6*|Gsf}3TC#oz^r%1rqK4x!^*xqiSecPu3NNnms3`e6{}ls_8B#4_mTw%iJUZ<~?<@wOSuy@|Jog9jfwQ>wOUVsMC;{(R#8?!$bnSUf2J'
    '{ldm5!)E~xE8g>!;Z5W}!%bcD#{y)+2V6aKoJmKx_v~74iCZs<xq}C}_JB{IHNr(cMKcY5SAgJ?41_W5z~1=t0U8kM764yGEEu5nE&+hAWr5leBLLt2z+X}sX&1`yUvtB~Sj0@o#B72FlwzW-NdW_B'
    'CkJXVV|UQ6cbIlLm&%SL7LXYNBi+&DgY*i<tST_3ywSwQbR7b;KEN0S8DA0l$da9YDKz$fm7u{}gZeK+hs)r+xO<@2ghH_@{R~wT`66?QT$<#$^dU7jT;`J7JG17fr1PjS->e){9mcwXrIj|PsPNAk'
    'Q6f*%%(#-xxPXKYoo4;X9ZY+`#rh_r$<&_H&{aiz60an%+TS!gO47+9Bg%JWM0q45-%b{kCkt8;=WNz-Q%ziju)DL>G!7Qi02>x+qTj7%snFrq<X16vM#ZvS#Mme~SKd_06m_R3KJo4}oZqdBgmLq1'
    '?U_dw7Hj~W7MFp1I|*equV_AKjFcb?LqbgvOL_c5dXFnc$d~jU*R51}(x&8*(_FS&88cTcH`aLnju~8p2PI!`0vF+#Ks{l^mHBx=!H#Nv)6fi{K5b}*l3qA8gYfqZadA047mH(eh%@8RwcEWj8=qxs'
    'HOPH0mc6%|2rWsApCqT35_0_WYTkDccgP2qHzy`mfhIrN{qu_+&zygt+sJuidnAWHZKl_E>=V*Zt21bwNZI!bTXJDbep9yOneWXL7hl(#{JM(bnLkf9wZsyU$VT4iC3qw_T&9GokV07eh3teA{~_?`'
    'PD>SM3P%uf`rrg_SQ@qy3?d1rVIPj-`a+XZ0Ze;BRdYBV>j7-kB9-f1+nG^|cSqAt!AoKadt|=78K+rH&=tu>H1F)J6uYG8&{CKAtRAt1y9(!@EO)4RH+s=ysI<RrKju`L3&XP=Qq37=%;#44N>fHC'
    'eyPwKUDXiN3g~&Vc`^gEN@c4fy7F%6jTzlIACr`V^)g3F3jBF9j^tnn8qmLvAEq1{yqlaQuQ}B!%oCCeUQRmdCIw;yJ>QHJh%q&%Q&c;$JCAS>7q1VZjKevNt5Xjs$~kn?w*qp!7m$8r&)U|+U@p3W'
    'Wdyk4&Wll8==ZB;gU$$7Qk-f=PT_85Qjn8ZuBz6+mavJQsrCS_+7oF#w8XPp9wW+VoS$2dOarXhZOr;x+ItD>H9F0)|2ad;Y6c_8H27^5Op1rxi%_g06sriuDnhY}P^=;ps|dv^La~ZatRfVv2*oNw'
    'vEEQ9R=f4f1zgPb9ea4@c0YYSbvo|g%>Lj=kuzd}d*1ECV+*vBaNR3GIhRfjsPk55m{!(2>oy_lm6HZ=YWLf%=4Rne!o4x#7B$O=Md|$(=&8fCb2d>KAf(d_;G1}{jWhU&G$I-8_6R5Y&S~r1al6L@'
    'r+;ZfNAXp2tyW7qV#JiYOM80<>nN^Oa>)b(MV)IRItjs-jyp_yV`a0EH;5p6dj)5QPyG7wi*eoBFQUL+-OW9=ec{!(xVulkyAS{PdgssG=-&I{=es4AZlWJ?N34y@lLZhccjO!|JdEZoV|-C~wZ+`{'
    'B<Q+mBatuY#kz^*p6Z-TapU(XCMN|AjwjdLGy4P>D&XhOw9j)rXCb{rz?p*$D{%q{Io=FCXjmD$1`XfI;MOWaVkFt=6Rx3&oXOnHx}z+@e`&`KpRi+04ftzEs<Ey|Omb;%K03KmGyjr$WwX2s5b_KY'
    'GqY!094Qw=x86;RJ%+M%8$#aPbdh4LU^KoZ?zw3*PCZSe(2BI4f23uoG!0dmY<Q@el0ZE7jLA*d-of({#ueY(1nqw>LBx@zk<!Mt#exDQ=_|kDSC3-YzvXZ<$#Xnimln7#A~CAO(*5NgdlLL5-r;7H'
    '6@g~o_w@Fo`1s?+nc>JSZ66U2`_fb}nhMJ6BEyo^ricoA%TZz4x#NcmiOMhrK67}~=C5Fwf|$fNrqd3@8@SzM<RSlC#y*A1J8%9yk5?CdJ#XHxr|?23ybua6gu)A<@IolO5DG7Z!VBSLyb#V?&3?Ce'
    '*6JCrhLh4}tKV#km%>R=_fiT@PYMRVT-becoxal?+MUxBjKh8_Da`OMI6t=AcBe^GSJ@~3z8K)L-P%D)VETdTm4Lzb4g`M$c<QMQxvSpy;hDp32ZCH{yZ_ivU{3n>$CK{IjtH_xof_V^hNyb;143j&'
    'L~H_4+x=OF=sQEZ)saE=@YN#Ww%c~>6Sr-j;#{j;Oe-k8v~(~$aY+ycsKd3S;H)*k{cGA#@(xNkCPdV!gL>II?U)CejAq^1*(<K(i(vY<nwXWRQPeV_CW%F()vQE+zzEVm(co#F=KCw+GzB~2h7>8W'
    'Dd4PTAQiiBz<S8B;&h{Vv!AA9BdTd>V;QQdDY>bVNcQGFSZwCdu$WKbR2nYONj-|_p9?RFf(M_yxy@gEYt-IWczl{+oLz(&#f}@F(I3X$>aV=<`tIQPQet+ms>55(u*3s1q)qroGR=#V0)(@qI~c&@'
    'lj>W#d|DY^*-dI4CUCm{f)o-@pO`ma6s$Aur#)wnuMCrQfnOw)%|skgB2umw)>2`9?H-4gCqyKd4`uV??9ofyz9MNVE?&Ry;&oFNzMVVQ@4c{-l1u2vp7PV(<jGkZQkr`G2^`>kZg$m$)O|#Rx0;F%'
    'cT0C(B&kqjtU$}OI`D|FxdtxL;IVNLTOWmcL~iEhs$$(>k_3pvcv(-oWh3G66QA0a^1SA%nFi{cz7PxiB(AF1<`LbmeVIA9rDS3YF7b65TpXXb2H;4hxi}dbs<Muf1!SB4N+w-ulf+j1m^ODdZ4>GW'
    'ccuv{>2@<%-b{V>K8Qd8G7GE(0%A29mo*G)a$T70Jo3UQ;YrUuLBa5%ME^GE^&&Doy+wjU({u!s+4(PIuCQgTB%t0Akm2*ASroz2CnGDPl~Xsfq(}%{p~}@qbtBHI0q0oCE`hacd@Hc1qdgKEzRi>L'
    'n>2F99yBc7gai!E?5<*rQmw1u1D@k@Z>xJ_$a1cJO!})JRcx)3;Pw`uS=J5lC@{1W<ZXs6r2#N>>CNx_lDS^R#G!KL4Fw$n+!M_CeS@sbR@8Jr!G03z=+F<|l7g4O<~v)VlhwAhkGp_x-#C_%&~(+>'
    'Gs`%j)Ab#`c?5Se58K0+&<cK~$^`cx(7Hedej-&;-hmhIYY^NV`@R@#lPP{Pk{gPL{lEapw)LNMI54>(&?DtInt?gNE>}sff!%YV%Ar+#L^IXA?a*alM0p5X2b^7(@Md=j;VMhsF)!n~luJ!`N{^*H'
    '_9D}fx*?c3lZ$_LtWGUuXZ42l-b0F{#tqX>wSJ4Dw^62tiNt@XekpGH$?<n$n9y>E4Jwyl8bb4C#>`j}4p31A?F5ed_?v`EXsIm!GN_;en`xIg{%tG$>LmqJG9)P}Q{*00Me58Ijxxy7ZhLeTWyO+{'
    'PD@HdDYr&ujJnlFZbQbX+%g%6Uz0`4Yz=;dH(#cGSjVRtjOpU1$aCcfa1TTbjQwC<xCa*QfrWcu;T~AH2Nv#ug?nJ(9$2^s7Vd%1>>h{?5<>@_9!$=GgO1(&(1Vw}O-W;t(o4J3YPW4;S+9i-Jk7IK'
    '*H}6jqNCTb)9-&a7WeHzFDXs;6D(ZV3KzEGZSn7WTYR;E<;X>w)pdxE8AQ8{_`2;)7x!MHwp-g{^s<aD7>-^v&DG2;aO1<WaqJmXOI)Q+U|<)4d;{=-wtBVo;4N9sEA)%l2=Iq*N`eijsZc|Zu?>&z'
    'Oh`3h3%r=W0K?8%S_Pb`Lqxno7yvKXAOr-E80t%K-GK|i1F9spk7<VogE2=$1oVIMV+exAC$UBR%=iQUmkKDK(Ep^*3ByFf*jK^8BDezIOwrOn2Vfe^0{+mAu;^8B0o|<0pM=Z8D#z?Xvk-EtuVzA`'
    'b((jWo)P4ij|3>;fdr&N1(TIG6~D=E0;qeL=vhE7NY_6Du;vK>-Oioyusg*kywIMCE%}ZX8m!oGrd@3z*-<a`@n9l2!?fiAz6cZcLcpeEVFK6wSF%$PwsIW;BN;J48;eb{6_<fvksH%%qYAj?t1n_8'
    '64>+Vk=~|ggJ$1kzaiQXPP}snKJa+OyN*f>oGDzTJ-k5FcK5*xF`krja9WTv@v0t#zlxL1Y;&qm=icGor93PZu@}O5*M!9$Ew+BVM)rl8jC3>{k?^d-o09dEixKD&yRA>IH>gSth48#Q{H=D+WR&<O'
    'KZs7*Oh|;wQ-bfO1UL0U%`tPXm_^nlSgAWtMQFq{pM<$2P?IvHHkeNIaT%2+WoB(QU;dRkT~hcfy=}rL$$>OU4mimkI>OKWiEPFo0$8_9?`?>emTceP{0!#F^w1CQLZ%~LBcTfJzWEL(PF_Nx`Xn4<'
    '@?+kE17UbYPVc;l^!L+VVV<VKOSkaSebbqdbokv`k;3S0r!acWIg1SHtfo^6i6@PRG1GOJuB00CI}&Y#KS5^DcGJ*_I<Hv~5OfZ-rV-RBZcAomUid1z70?s8wjn-)|5S#m{v6&@ntO*yquIc@Ba4MU'
    'f@{WV8Qcap_+ICAKV9E*j*r{UKs4o#m`$CPeHsXccJ|Tq?cDIKZTR+yd>p4gIuEW%t#%tfT7ZetbV7XKQ;0{yg&oBhs%lB8wykcWSMy_g@WBD6sP2bjyZHgt+SkB1)Oq(D(Q|PwKUx14?-J-i*1N&R'
    'LL?J(CJAm5%wU^4Eao<tPR-#hxI}`De1C2Pg#r#~G-4=&UY8?yOiq#FnuAGM2LwczU~m|PN>oLN(Gj9^^o3qu<kP!iUf_W)><a>`JJ2Yutx}8!hWz4x#rHx0#A=$ti&6uHh*@z&;#Lv|ATg|^qC~Y+'
    '#7Lcr6hkxCkh`(}2f2~`@70##JcWwOdLRg|1iLHiWA4q7*Vy$YlM=&KHUI&um;#sr_lTe*DZpo=kfg_iBT21o6pVx?iCA?{mMlS0;M^Kj|M9Lq7SjdLlhrG_uUh!m*Hb@|v>I8(WGakuyO7Ll`Elpu'
    'yR^FHSY6pV@;uAyB#1oJ(}@wB6-qUz3Z4~KCWA;}Wrm;vYKcy{bxB|Op4}3y3g(8UXvqh9q8gIvIY~P3CwA&a!>qT|)svALrN&It+-s*?POCDikCPJ>kFF}Idd`luSFVq>s4%%61bQhIRXdK>Z?$C{'
    '?4^9HjW^!gpFu1H4(1FV;R2N2bhiC9{Z?=7%h)Emg~J|SxKht~j|u*Om&LKdq|`WSSgMYW;}3A$L861JudCCAN9ZM36vZCF;87^4O&n!YehQwMtzUZ;YQYoZ;mlUAJ#00^6G*W@t}%0MVCrI)ThT6>'
    '&z#N;mTRl-n5qW1+LY!?fPVU^>$Ya0*;*#rL#vt>uiBrQ$R_DFKr!t<(kKiTO+HZNiiAo@TOyP8*k(XeVfI8*Lz<w=IZ7nk#4EEp(rZXjQ5q*f=gC*yOleZqOjbd~58qM@H&~BZgbPhugGKnotWO)6'
    'k5&&wP|pt>)FZq!ZxMy@xt^A%L;{yz^!ayaaI>OZPqr&hzk{2dNo1-bhp|uh&tkeQke=saczO^w9SY@Hdu4gmU$-|Se9^&_NfyJwG-`8U;PWq6{ak`kgvk|Qaz&V25hhoJ$rWL8MVMR>CigO7au=8G'
    'Woyvw8{_17;b*7a?tT<*$$5!=e(dy31>L^gIdx1WedomV`P@ErIzu~&h#U6p6X)a=683ir)q7pBT1E8W4;?+|p}o|*^W8AMN9yD10rN{Sq><~4^hgp?H@U7+RuS3NK>}_xm>>VTJG#_+9ueQG3`YTY'
    'D9kZQQzA{cbIybN5TN;(C!XMK<;yRk1B&Q?A1OLObIMoW5XXKzn#!d-nXLHr@2m+6DDhYXN~-owyr!@{VS`1C!OO=Oz@`!69JOwU=A!>c?9a);nI4PN{IscClEFlkNX-ANlNd>Z7Nh?%w%XJPXTG1v'
    'sPaEZ93qC&fKI6r^Vp)raIQ|aZwYcFLgCw1_KP%t6%o=xeyxgkJE^Yb2Ze7(3H>|p@D~ID@fvmgRS-sSbdOeN7w+l^$;7XMU%*O^{qn2Yg7#wKmx#EWXV5496kn58Q@3{BCIMxyj;PDJK`7E59Ffju'
    '7;AYfMxPjjicFfXXm*9ayO`(bI6n;#qo01x7?$<N%$e^LyqT=tNpkqqlMppWClTf9)fRJlmXKsfv|O9I+oAaZ5A%tWBEOVB!|{70iCL=ZyLOhzos}Fh=yX~$o1__~D>*3>NZFW)8;W86WXQy0rhBfL'
    'EpGqB4QG>yJwuaY9(&Ke9dZNK4>h;hOx%B&?dcUv+)cK|yi;P+UGOP(!W=U>??gVzGm-PIFsT!HiB$gQp2XNV{X<URy?+(@<#Xzn_u+KnPJ*R>1B7`~mq+BM%Wt;iHu6gDx}!h6#Hr`DjDC-Vn=Pw&'
    'ShCMUXz+Ib@pFoh8he~1iBEe&Bb_Iv-JIhxql!{5Wn^)sXbe)Co07ay3VF9eL*|#Y2HdCDGtGNp?rkqsP1JWQVHL={_8FzUC@H^dX>RA4RvTrVdCjRMo-HRr`gPNDq(tB+2x{e~%*s4iY>**=x{hni'
    'NOfmqOQ=NFn)hV%S39KIc^QaxFqsXhYS|00AR%Yd?k6?#c3s@N`OQ+suD(I{H}ANCm<<`AW60$O!^~u|3}hJ3Qv7_sPZA7Fp^TB}Tf-A0UnB&ZzGrEg2b@V+X89N9l8J`LFw2BTubLuCMvNO>c>f&}'
    '#-Jjk!g$jn?x%?RDdK*LxSt~Kr-=J0;(m&_pCaz3i2Etxeu}uCBJSr6#r+K0j?;5{U2}X*QaZSBPNc`NcuCtnKXyNMyKQ4>uiO6Y42Dt&PEy+W+=hH`hLUD?IHW}>K|lt|tMJ;6k+Q6KomK~u0(JYJ'
    '-N6Uvqx;@&q95+@XNEVEA>`ej)Sf}{{y{chQehYm>hMwmV?^@AbZ!c(d;15xe$Q^fRotc1hg^KLw<L%6yQ?{A(#-(cqbR!X-w&Lj+q8R>k@)LJyMKPsbBC?whXMZ13eFw7<J#@sna$Ba$zagBblhJq'
    'x<ki3ZrKA;b8Xio?p61*_+Q;)JujY6D}tbkC)B<>EDt}X{?f@Z0og-1UCpq!h#{tevKPWgIGj0rg+j(*>`fC`p@AI%3nyCwhX4_sT8(XD8T4~oZUw-%g|?uU*o^*kofqA^U;$;PCc((gMnTR|n0^as'
    '^uRG>5$29KLjF&aYYfW(T1(5>s~+9ebinl|Nm#pCqFU@+@u*a_`BT)Y&Pjw(W18JC8ROfj7sviOk1=7X<Tu4fPkf7C<&BN?#txs{H9>1maU2jPzyjX*32$$aoHF6Z(THqk45#E}IisS$o^*_3e7kN^'
    'w5WF+X+ZK2z$`%6gE@&c1r|_L^pj|uXYZ`w6s%AW(u(3Aq>gZ;z+Fn4gjZXn%YecqRi!+*qPrT$qeyI0uuHgDVlPtG#MdYZ%_8EYB71MEAtFn84O6R0p9F)WmrR(d7Rpb=uzz;Q>yrvF1afJ#u(vP?'
    '8nclV#!>6nQNz-dS2Y``{}6c0FM|wk)!0uZUJr{BRUGt{q^fAr27?I98WqYitLNJZm8yNSY$A(^CfX>;2Q?ZQ<jsAiE@U1wHtz|YSFoyzWUFCl1Ugw)qN(pM(Da&Y@ERIH(x^S7-ZL5-9q!EMA7Q^G'
    'VUT7mP0o{Rj*m8wp!pvfj;9(0MombuUS!30Z%n212%J3hnI3{^FJcv;-$m&64;1?S-4DPi8^bz_nxy;hY0oTWJ|(Aus!Buokx$G~NJH?p(77B2D>eK0HWnO$qP#xdJRv4Wq`5$O5o7*#-m%MboR=aU'
    '47Y*orCBKh{v-UD)7+SK<AL4`j)Op(uwtpwFHDqx3FEb!uyqTM7pI;0{x+W5kFvw$2!P3z9*FoOA;lMMANawAY|Bo@+Y6G@H%EweQ`2>Y#E|M<ZF_rfzntQJsl|51AzC3OYG9XmzB2`Gv0CLkj>kDo'
    'G5I~x75wH?#|GZm;#|p;uD_rE>9=qH4*>o4{{'
)


class _Log:
    def __init__(self):
        self._buf = ""
        self._cap = 3750

    def print(self, *args, sep=" ", end="\n"):
        self._buf += sep.join(map(str, args)) + end

    def flush(self, st, orders, conv, td):
        base = len(self._ser([self._comp_state(st, ""), self._comp_ord(orders), conv, "", ""]))
        cap = (self._cap - base) // 3
        print(self._ser([
            self._comp_state(st, self._clip(st.traderData, cap)),
            self._comp_ord(orders),
            conv,
            self._clip(td, cap),
            self._clip(self._buf, cap),
        ]))
        self._buf = ""

    def _comp_state(self, st, td):
        return [st.timestamp, td,
                [[v.symbol, v.product, v.denomination] for v in st.listings.values()],
                {s: [d.buy_orders, d.sell_orders] for s, d in st.order_depths.items()},
                [[t.symbol, t.price, t.quantity, t.buyer, t.seller, t.timestamp] for a in st.own_trades.values() for t in a],
                [[t.symbol, t.price, t.quantity, t.buyer, t.seller, t.timestamp] for a in st.market_trades.values() for t in a],
                st.position,
                [st.observations.plainValueObservations,
                 {p: [o.bidPrice, o.askPrice, o.transportFees, o.exportTariff, o.importTariff, o.sugarPrice, o.sunlightIndex]
                   for p, o in st.observations.conversionObservations.items()}]]

    def _comp_ord(self, orders):
        return [[o.symbol, o.price, o.quantity] for a in orders.values() for o in a]

    def _ser(self, v):
        return json.dumps(v, cls=ProsperityEncoder, separators=(",", ":"))

    def _clip(self, v, mx):
        lo, hi, out = 0, min(len(v), mx), ""
        while lo <= hi:
            m = (lo + hi) // 2
            if len(self._ser(v[:m])) <= mx:
                out = v[:m]; lo = m + 1
            else:
                hi = m - 1
        return out


def _unpack():
    return json.loads(zlib.decompress(base64.b85decode(_PACKED)).decode())


def _silent(*_a, **_k):
    pass


def _init_trader(label, code):
    ns = {"__name__": f"_sub_{label}", "print": _silent}
    exec(code, ns)
    return ns["Trader"]()


def _split_state(raw):
    if not raw:
        return {}
    try:
        d = json.loads(raw)
    except Exception:
        return {}
    return d.get("sub", {}) if isinstance(d, dict) else {}


def _ser_sub(val):
    return json.dumps(val, separators=(",", ":")) if not isinstance(val, str) else val


def _deser_sub(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return raw


_CFG = _unpack()
_PRODUCT_MAP = {n: set(ps) for n, ps in _CFG["products"].items()}
_ALL = set().union(*_PRODUCT_MAP.values())
assert len(_ALL) == 50, f"Expected 50 products, got {len(_ALL)}"
_TRADERS = {n: _init_trader(n, src) for n, src in _CFG["sources"].items()}
_log = _Log()


class Trader:
    def run(self, state: TradingState):
        prev = _split_state(state.traderData)
        nxt = {}
        combined_orders = {}
        total_conv = 0

        for name, trader in _TRADERS.items():
            sub_state = TradingState(
                _ser_sub(prev.get(name, {})),
                state.timestamp, state.listings, state.order_depths,
                state.own_trades, state.market_trades, state.position,
                state.observations,
            )
            orders, conv, td = trader.run(sub_state)
            allowed = _PRODUCT_MAP[name]
            for sym, ol in orders.items():
                if sym in allowed and ol is not None:
                    combined_orders.setdefault(sym, []).extend(ol)
            total_conv += conv
            nxt[name] = _deser_sub(td)

        td_out = json.dumps({"sub": nxt}, separators=(",", ":"))
        _log.flush(state, combined_orders, total_conv, td_out)
        return combined_orders, total_conv, td_out
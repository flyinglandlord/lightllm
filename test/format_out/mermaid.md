```mermaid
flowchart LR
0["id: 0
(nt(root) = [@, t({), nt(reasoning), t(,), nt(conclusion), t(})] # la = (t(),))
"]
1["id: 1
(nt(root) = [t({), @, nt(reasoning), t(,), nt(conclusion), t(})] # la = (t(),))
(nt(reasoning) = [@, t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
2["id: 2
(nt(root) = [t({), nt(reasoning), @, t(,), nt(conclusion), t(})] # la = (t(),))
"]
3["id: 3
(nt(reasoning) = [t("), @, t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
4["id: 4
(nt(root) = [t({), nt(reasoning), t(,), @, nt(conclusion), t(})] # la = (t(),))
(nt(conclusion) = [@, t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
5["id: 5
(nt(reasoning) = [t("), t(r), @, t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
6["id: 6
(nt(conclusion) = [t("), @, t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
7["id: 7
(nt(root) = [t({), nt(reasoning), t(,), nt(conclusion), @, t(})] # la = (t(),))
"]
8["id: 8
(nt(reasoning) = [t("), t(r), t(e), @, t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
9["id: 9
(nt(conclusion) = [t("), t(c), @, t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
10["id: 10
(nt(root) = [t({), nt(reasoning), t(,), nt(conclusion), t(}), @] # la = (t(),))
"]
11["id: 11
(nt(reasoning) = [t("), t(r), t(e), t(a), @, t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
12["id: 12
(nt(conclusion) = [t("), t(c), t(o), @, t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
13["id: 13
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), @, t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
14["id: 14
(nt(conclusion) = [t("), t(c), t(o), t(n), @, t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
15["id: 15
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), @, t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
16["id: 16
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), @, t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
17["id: 17
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), @, t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
18["id: 18
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), @, t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
19["id: 19
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), @, t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
20["id: 20
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), @, t(s), t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
21["id: 21
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), @, t(g), t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
22["id: 22
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), @, t(i), t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
23["id: 23
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), @, t("), t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
24["id: 24
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), @, t(o), t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
25["id: 25
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), @, t(:), t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
26["id: 26
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), @, t(n), t("), t(:), nt(string)] # la = (t(}),))
"]
27["id: 27
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), @, t([), nt(reasoning_steps), t(])] # la = (t(,),))
"]
28["id: 28
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), @, t("), t(:), nt(string)] # la = (t(}),))
"]
29["id: 29
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), @, nt(reasoning_steps), t(])] # la = (t(,),))
(nt(reasoning_steps) = [@, nt(reasoning_step)] # la = (t(]),))
(nt(reasoning_steps) = [@, nt(reasoning_step), t(,), nt(reasoning_steps)] # la = (t(]),))
(nt(reasoning_step) = [@, t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
30["id: 30
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), @, t(:), nt(string)] # la = (t(}),))
"]
31["id: 31
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), @, t(])] # la = (t(,),))
"]
32["id: 32
(nt(reasoning_steps) = [nt(reasoning_step), @] # la = (t(]),))
(nt(reasoning_steps) = [nt(reasoning_step), @, t(,), nt(reasoning_steps)] # la = (t(]),))
"]
33["id: 33
(nt(reasoning_step) = [t({), @, t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
34["id: 34
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), @, nt(string)] # la = (t(}),))
(nt(string) = [@, t("), nt(string_6), t("), nt(ws)] # la = (t(}),))
(nt(string) = [@, t("), t("), nt(ws)] # la = (t(}),))
(nt(string) = [@, t("), nt(string_6), t(")] # la = (t(}),))
(nt(string) = [@, t("), t(")] # la = (t(}),))
"]
35["id: 35
(nt(reasoning) = [t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t("), t(:), t([), nt(reasoning_steps), t(]), @] # la = (t(,),))
"]
36["id: 36
(nt(reasoning_steps) = [nt(reasoning_step), t(,), @, nt(reasoning_steps)] # la = (t(]),))
(nt(reasoning_steps) = [@, nt(reasoning_step)] # la = (t(]),))
(nt(reasoning_steps) = [@, nt(reasoning_step), t(,), nt(reasoning_steps)] # la = (t(]),))
(nt(reasoning_step) = [@, t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
37["id: 37
(nt(reasoning_step) = [t({), t("), @, t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
38["id: 38
(nt(string) = [t("), @, nt(string_6), t("), nt(ws)] # la = (t(}),))
(nt(string) = [t("), @, t("), nt(ws)] # la = (t(}),))
(nt(string) = [t("), @, nt(string_6), t(")] # la = (t(}),))
(nt(string) = [t("), @, t(")] # la = (t(}),))
(nt(string_6) = [@, t(ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~), nt(string_6)] # la = (t("),))
(nt(string_6) = [@, t(ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~)] # la = (t("),))
"]
39["id: 39
(nt(conclusion) = [t("), t(c), t(o), t(n), t(c), t(l), t(u), t(s), t(i), t(o), t(n), t("), t(:), nt(string), @] # la = (t(}),))
"]
40["id: 40
(nt(reasoning_steps) = [nt(reasoning_step), t(,), nt(reasoning_steps), @] # la = (t(]),))
"]
41["id: 41
(nt(reasoning_step) = [t({), t("), t(r), @, t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
42["id: 42
(nt(string) = [t("), t("), @, nt(ws)] # la = (t(}),))
(nt(string) = [t("), t("), @] # la = (t(}),))
(nt(ws) = [@, nt(ws_9)] # la = (t(}),))
(nt(ws_9) = [@, nt(ws_8)] # la = (t(}),))
(nt(ws_8) = [@, t(ĊĠ     ), nt(ws)] # la = (t(}),))
(nt(ws_8) = [@, t(ĊĠ     )] # la = (t(}),))
"]
43["id: 43
(nt(string) = [t("), nt(string_6), @, t("), nt(ws)] # la = (t(}),))
(nt(string) = [t("), nt(string_6), @, t(")] # la = (t(}),))
"]
44["id: 44
(nt(string_6) = [t(ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~), @, nt(string_6)] # la = (t("),))
(nt(string_6) = [t(ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~), @] # la = (t("),))
(nt(string_6) = [@, t(ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~), nt(string_6)] # la = (t("),))
(nt(string_6) = [@, t(ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~)] # la = (t("),))
"]
45["id: 45
(nt(reasoning_step) = [t({), t("), t(r), t(e), @, t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
46["id: 46
(nt(string) = [t("), t("), nt(ws), @] # la = (t(}),))
"]
47["id: 47
(nt(ws_9) = [nt(ws_8), @] # la = (t(}),))
"]
48["id: 48
(nt(ws) = [nt(ws_9), @] # la = (t(}),))
"]
49["id: 49
(nt(ws_8) = [t(ĊĠ     ), @, nt(ws)] # la = (t(}),))
(nt(ws_8) = [t(ĊĠ     ), @] # la = (t(}),))
(nt(ws) = [@, nt(ws_9)] # la = (t(}),))
(nt(ws_9) = [@, nt(ws_8)] # la = (t(}),))
(nt(ws_8) = [@, t(ĊĠ     ), nt(ws)] # la = (t(}),))
(nt(ws_8) = [@, t(ĊĠ     )] # la = (t(}),))
"]
50["id: 50
(nt(string) = [t("), nt(string_6), t("), @, nt(ws)] # la = (t(}),))
(nt(string) = [t("), nt(string_6), t("), @] # la = (t(}),))
(nt(ws) = [@, nt(ws_9)] # la = (t(}),))
(nt(ws_9) = [@, nt(ws_8)] # la = (t(}),))
(nt(ws_8) = [@, t(ĊĠ     ), nt(ws)] # la = (t(}),))
(nt(ws_8) = [@, t(ĊĠ     )] # la = (t(}),))
"]
51["id: 51
(nt(string_6) = [t(ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~), nt(string_6), @] # la = (t("),))
"]
52["id: 52
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), @, t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
53["id: 53
(nt(ws_8) = [t(ĊĠ     ), nt(ws), @] # la = (t(}),))
"]
54["id: 54
(nt(string) = [t("), nt(string_6), t("), nt(ws), @] # la = (t(}),))
"]
55["id: 55
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), @, t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
56["id: 56
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), @, t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
57["id: 57
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), @, t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
58["id: 58
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), @, t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
59["id: 59
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), @, t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
60["id: 60
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), @, t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
61["id: 61
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), @, t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
62["id: 62
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), @, t(t), t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
63["id: 63
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), @, t(e), t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
64["id: 64
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), @, t(p), t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
65["id: 65
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), @, t("), t(:), nt(string), t(})] # la = (t(,), t(])))
"]
66["id: 66
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), @, t(:), nt(string), t(})] # la = (t(,), t(])))
"]
67["id: 67
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), @, nt(string), t(})] # la = (t(,), t(])))
(nt(string) = [@, t("), nt(string_6), t("), nt(ws)] # la = (t(}),))
(nt(string) = [@, t("), t("), nt(ws)] # la = (t(}),))
(nt(string) = [@, t("), nt(string_6), t(")] # la = (t(}),))
(nt(string) = [@, t("), t(")] # la = (t(}),))
"]
68["id: 68
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), @, t(})] # la = (t(,), t(])))
"]
69["id: 69
(nt(reasoning_step) = [t({), t("), t(r), t(e), t(a), t(s), t(o), t(n), t(i), t(n), t(g), t(_), t(s), t(t), t(e), t(p), t("), t(:), nt(string), t(}), @] # la = (t(,), t(])))
"]

0 -->                     0_{_1 ---> 1
1 -->                     1_reasoning_2 ---> 2
1 -->                     1_"_3 ---> 3
2 -->                     2_,_4 ---> 4
3 -->                     3_r_5 ---> 5
4 -->                     4_"_6 ---> 6
4 -->                     4_conclusion_7 ---> 7
5 -->                     5_e_8 ---> 8
6 -->                     6_c_9 ---> 9
7 -->                     7_}_10 ---> 10
8 -->                     8_a_11 ---> 11
9 -->                     9_o_12 ---> 12
11 -->                     11_s_13 ---> 13
12 -->                     12_n_14 ---> 14
13 -->                     13_o_15 ---> 15
14 -->                     14_c_16 ---> 16
15 -->                     15_n_17 ---> 17
16 -->                     16_l_18 ---> 18
17 -->                     17_i_19 ---> 19
18 -->                     18_u_20 ---> 20
19 -->                     19_n_21 ---> 21
20 -->                     20_s_22 ---> 22
21 -->                     21_g_23 ---> 23
22 -->                     22_i_24 ---> 24
23 -->                     23_"_25 ---> 25
24 -->                     24_o_26 ---> 26
25 -->                     25_:_27 ---> 27
26 -->                     26_n_28 ---> 28
27 -->                     27_[_29 ---> 29
28 -->                     28_"_30 ---> 30
29 -->                     29_reasoning_steps_31 ---> 31
29 -->                     29_reasoning_step_32 ---> 32
29 -->                     29_{_33 ---> 33
30 -->                     30_:_34 ---> 34
31 -->                     31_]_35 ---> 35
32 -->                     32_,_36 ---> 36
33 -->                     33_"_37 ---> 37
34 -->                     34_"_38 ---> 38
34 -->                     34_string_39 ---> 39
36 -->                     36_reasoning_steps_40 ---> 40
36 -->                     36_reasoning_step_32 ---> 32
36 -->                     36_{_33 ---> 33
37 -->                     37_r_41 ---> 41
38 -->                     38_"_42 ---> 42
38 -->                     38_string_6_43 ---> 43
38 -->                     38_ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~_44 ---> 44
41 -->                     41_e_45 ---> 45
42 -->                     42_ws_46 ---> 46
42 -->                     42_ws_8_47 ---> 47
42 -->                     42_ws_9_48 ---> 48
42 -->                     42_ĊĠ     _49 ---> 49
43 -->                     43_"_50 ---> 50
44 -->                     44_string_6_51 ---> 51
44 -->                     44_ĠĊ !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~_44 ---> 44
45 -->                     45_a_52 ---> 52
49 -->                     49_ws_53 ---> 53
49 -->                     49_ws_8_47 ---> 47
49 -->                     49_ws_9_48 ---> 48
49 -->                     49_ĊĠ     _49 ---> 49
50 -->                     50_ws_54 ---> 54
50 -->                     50_ws_8_47 ---> 47
50 -->                     50_ws_9_48 ---> 48
50 -->                     50_ĊĠ     _49 ---> 49
52 -->                     52_s_55 ---> 55
55 -->                     55_o_56 ---> 56
56 -->                     56_n_57 ---> 57
57 -->                     57_i_58 ---> 58
58 -->                     58_n_59 ---> 59
59 -->                     59_g_60 ---> 60
60 -->                     60___61 ---> 61
61 -->                     61_s_62 ---> 62
62 -->                     62_t_63 ---> 63
63 -->                     63_e_64 ---> 64
64 -->                     64_p_65 ---> 65
65 -->                     65_"_66 ---> 66
66 -->                     66_:_67 ---> 67
67 -->                     67_"_38 ---> 38
67 -->                     67_string_68 ---> 68
68 -->                     68_}_69 ---> 69
```
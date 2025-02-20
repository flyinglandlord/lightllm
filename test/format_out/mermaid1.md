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

36 --> t:{#pop:36,#push:36,33#s:36#e:33 ---> 33
49 --> t:ĊĠ#pop:49,#push:49,#s:49#e:49 ---> 49
44 --> t:ĠĊ!#$%&'*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~#pop:44,#push:44,#s:44#e:44 ---> 44
0 --> t:{#pop:0,#push:0,1#s:0#e:1 ---> 1
1 --> t:"#pop:1,#push:1,3#s:1#e:3 ---> 3
2 --> t:,#pop:2,#push:2,4#s:2#e:4 ---> 4
3 --> t:r#pop:3,#push:3,5#s:3#e:5 ---> 5
4 --> t:"#pop:4,#push:4,6#s:4#e:6 ---> 6
5 --> t:e#pop:5,#push:5,8#s:5#e:8 ---> 8
6 --> t:c#pop:6,#push:6,9#s:6#e:9 ---> 9
7 --> t:}#pop:7,#push:7,10#s:7#e:10 ---> 10
8 --> t:a#pop:8,#push:8,11#s:8#e:11 ---> 11
9 --> t:o#pop:9,#push:9,12#s:9#e:12 ---> 12
11 --> t:s#pop:11,#push:11,13#s:11#e:13 ---> 13
12 --> t:n#pop:12,#push:12,14#s:12#e:14 ---> 14
13 --> t:o#pop:13,#push:13,15#s:13#e:15 ---> 15
14 --> t:c#pop:14,#push:14,16#s:14#e:16 ---> 16
15 --> t:n#pop:15,#push:15,17#s:15#e:17 ---> 17
16 --> t:l#pop:16,#push:16,18#s:16#e:18 ---> 18
17 --> t:i#pop:17,#push:17,19#s:17#e:19 ---> 19
18 --> t:u#pop:18,#push:18,20#s:18#e:20 ---> 20
19 --> t:n#pop:19,#push:19,21#s:19#e:21 ---> 21
20 --> t:s#pop:20,#push:20,22#s:20#e:22 ---> 22
21 --> t:g#pop:21,#push:21,23#s:21#e:23 ---> 23
22 --> t:i#pop:22,#push:22,24#s:22#e:24 ---> 24
23 --> t:"#pop:23,#push:23,25#s:23#e:25 ---> 25
24 --> t:o#pop:24,#push:24,26#s:24#e:26 ---> 26
25 --> t::#pop:25,#push:25,27#s:25#e:27 ---> 27
26 --> t:n#pop:26,#push:26,28#s:26#e:28 ---> 28
27 --> t:[#pop:27,#push:27,29#s:27#e:29 ---> 29
28 --> t:"#pop:28,#push:28,30#s:28#e:30 ---> 30
29 --> t:{#pop:29,#push:29,33#s:29#e:33 ---> 33
30 --> t::#pop:30,#push:30,34#s:30#e:34 ---> 34
31 --> t:]#pop:31,#push:31,35#s:31#e:35 ---> 35
32 --> t:,#pop:32,#push:32,36#s:32#e:36 ---> 36
33 --> t:"#pop:33,#push:33,37#s:33#e:37 ---> 37
34 --> t:"#pop:34,#push:34,38#s:34#e:38 ---> 38
37 --> t:r#pop:37,#push:37,41#s:37#e:41 ---> 41
38 --> t:"#pop:38,#push:38,42#s:38#e:42 ---> 42
38 --> t:ĠĊ!#$%&'*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~#pop:38,#push:38,44#s:38#e:44 ---> 44
41 --> t:e#pop:41,#push:41,45#s:41#e:45 ---> 45
42 --> t:ĊĠ#pop:42,#push:42,49#s:42#e:49 ---> 49
43 --> t:"#pop:43,#push:43,50#s:43#e:50 ---> 50
45 --> t:a#pop:45,#push:45,52#s:45#e:52 ---> 52
50 --> t:ĊĠ#pop:50,#push:50,49#s:50#e:49 ---> 49
52 --> t:s#pop:52,#push:52,55#s:52#e:55 ---> 55
55 --> t:o#pop:55,#push:55,56#s:55#e:56 ---> 56
56 --> t:n#pop:56,#push:56,57#s:56#e:57 ---> 57
57 --> t:i#pop:57,#push:57,58#s:57#e:58 ---> 58
58 --> t:n#pop:58,#push:58,59#s:58#e:59 ---> 59
59 --> t:g#pop:59,#push:59,60#s:59#e:60 ---> 60
60 --> t:_#pop:60,#push:60,61#s:60#e:61 ---> 61
61 --> t:s#pop:61,#push:61,62#s:61#e:62 ---> 62
62 --> t:t#pop:62,#push:62,63#s:62#e:63 ---> 63
63 --> t:e#pop:63,#push:63,64#s:63#e:64 ---> 64
64 --> t:p#pop:64,#push:64,65#s:64#e:65 ---> 65
65 --> t:"#pop:65,#push:65,66#s:65#e:66 ---> 66
66 --> t::#pop:66,#push:66,67#s:66#e:67 ---> 67
67 --> t:"#pop:67,#push:67,38#s:67#e:38 ---> 38
68 --> t:}#pop:68,#push:68,69#s:68#e:69 ---> 69
35 --> t:,#pop:35,31,29,27,25,23,21,19,17,15,13,11,8,5,3,1#push:1,2,4#s:35#e:4 ---> 4
42 --> t:}#pop:42,38,34,30,28,26,24,22,20,18,16,14,12,9,6,4#push:4,7,10#s:42#e:10 ---> 10
42 --> t:}#pop:42,38,67#push:67,68,69#s:42#e:69 ---> 69
44 --> t:"#pop:44,38#push:38,43,50#s:44#e:50 ---> 50
44 --> t:"#pop:44,44,38#push:38,43,50#s:44#e:50 ---> 50
49 --> t:}#pop:49,42,38,34,30,28,26,24,22,20,18,16,14,12,9,6,4#push:4,7,10#s:49#e:10 ---> 10
49 --> t:}#pop:49,42,38,67#push:67,68,69#s:49#e:69 ---> 69
49 --> t:}#pop:49,50,43,38,34,30,28,26,24,22,20,18,16,14,12,9,6,4#push:4,7,10#s:49#e:10 ---> 10
49 --> t:}#pop:49,50,43,38,67#push:67,68,69#s:49#e:69 ---> 69
50 --> t:}#pop:50,43,38,34,30,28,26,24,22,20,18,16,14,12,9,6,4#push:4,7,10#s:50#e:10 ---> 10
50 --> t:}#pop:50,43,38,67#push:67,68,69#s:50#e:69 ---> 69
69 --> t:,#pop:69,68,67,66,65,64,63,62,61,60,59,58,57,56,55,52,45,41,37,33,29#push:29,32,36#s:69#e:36 ---> 36
69 --> t:,#pop:69,68,67,66,65,64,63,62,61,60,59,58,57,56,55,52,45,41,37,33,36,32#push:32,36#s:69#e:36 ---> 36
69 --> t:]#pop:69,68,67,66,65,64,63,62,61,60,59,58,57,56,55,52,45,41,37,33,29#push:29,31,35#s:69#e:35 ---> 35
69 --> t:]#pop:69,68,67,66,65,64,63,62,61,60,59,58,57,56,55,52,45,41,37,33,36,32,29#push:29,31,35#s:69#e:35 ---> 35
69 --> t:]#pop:69,68,67,66,65,64,63,62,61,60,59,58,57,56,55,52,45,41,37,33,36,32,36,32,29#push:29,31,35#s:69#e:35 ---> 35
```
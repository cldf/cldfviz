from cldfbench.__main__ import main


def test_htmlmap(glottolog_dir, tmp_path):
    values = tmp_path.joinpath('values.csv')
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
1,abcd1235,param1,val1
2,abcd1234,param1,val2""", encoding='utf8')
    main([
        'cldfviz.htmlmap',
        '--glottolog', str(glottolog_dir),
        '--output', str(tmp_path),
        '--test',
        str(values)])
    assert tmp_path.joinpath('index.html').exists()

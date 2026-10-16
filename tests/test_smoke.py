"""Synthetic local fixtures only: no customer schematics or vendor datasheets."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import fitz
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
def run(script, *args, ok=True):
    p = subprocess.run([sys.executable, str(ROOT/'scripts'/script), *map(str,args)], capture_output=True, text=True)
    if ok and p.returncode: raise AssertionError(p.stdout+p.stderr)
    return p

def pdf_at(path, labels):
    doc=fitz.open();page=doc.new_page()
    for point, text in labels:page.insert_text(point,text)
    doc.save(path);doc.close()

class SmokeTests(unittest.TestCase):
    def test_index_cards_exist(self):
        cards=json.loads((ROOT/'knowledge_base/chip_rules/index.json').read_text())['chips']
        self.assertEqual(cards,[])
        for c in cards:self.assertTrue((ROOT/c['card']).is_file(),c['model'])
        self.assertIn('为空',run('kb_search.py','--list-chips').stdout)

    def test_chip_lookup_without_company_index(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'knowledge_base/chip_rules').mkdir(parents=True)
            (root/'knowledge_base/chip_rules/index.json').write_text(json.dumps({'chips':[{'model':'TEST-CHIP','card':'knowledge_base/chip_rules/TEST-CHIP.md','datasheet':''}]}))
            self.assertIn('TEST-CHIP',run('kb_search.py','--root',root,'--chip','TEST-CHIP').stdout)

    def test_vector_and_blank_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);pdf=root/'synthetic.pdf'
            pdf_at(pdf,[((72,72),'R1 10k VCC GND C1 100nF synthetic fixture')])
            run('extract_schematic.py',pdf,root)
            meta=json.loads((root/'output/_extract/meta.json').read_text())
            self.assertEqual(meta['page_count'],1)
            self.assertIn('R1',meta['unique_ref_designators'])
            self.assertIn('GND',meta['unique_power_nets'])
            blank=root/'blank.pdf';pdf_at(blank,[])
            run('extract_schematic.py',blank,root)
            self.assertTrue((root/'output/_extract/page_01.png').is_file())

    def test_ingest_no_card_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);pdf=root/'test.pdf';pdf_at(pdf,[((72,72),'Synthetic datasheet fixture')])
            run('ingest_datasheet.py',pdf,'TEST-CHIP',root)
            card=root/'knowledge_base/chip_rules/TEST-CHIP.md'
            self.assertTrue(card.is_file());card.write_text('manual review preserved')
            run('ingest_datasheet.py',pdf,'TEST-CHIP',root)
            self.assertEqual(card.read_text(),'manual review preserved')
            idx=json.loads((root/'knowledge_base/chip_rules/index.json').read_text())
            self.assertEqual(len(idx['chips']),1)

    def test_model_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);pdf=root/'test.pdf';pdf_at(pdf,[])
            for model in ['', '.', '..', '   ']:
                # Empty explicit model falls back to filename by documented behavior.
                if not model:continue
                p=run('ingest_datasheet.py',pdf,model,root,ok=False)
                self.assertNotEqual(p.returncode,0)
            self.assertFalse((root/'knowledge_base').exists())

    def test_import_checklist(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);xlsx=root/'synthetic.xlsx';wb=openpyxl.Workbook();ws=wb.active
            ws.title='硬件设计总体原则';ws.append([]);ws.append([]);ws.append([])
            ws.append([None,1,'SCH','电源','Synthetic power check','高']);wb.save(xlsx);wb.close()
            run('build_company_rules.py',xlsx,root)
            idx=json.loads((root/'knowledge_base/company_rules/index.json').read_text())
            self.assertEqual(idx['total'],1);self.assertEqual(idx['rules'][0]['severity'],'严重')

    def test_equal_value_labels_are_distinct(self):
        spec=importlib.util.spec_from_file_location('pairing',ROOT/'scripts/rf_dense_pairing.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            pdf=Path(d)/'labels.pdf'
            pdf_at(pdf,[((50,50),'R1'),((85,50),'10k'),((250,50),'R2'),((285,50),'10k')])
            refs,vals,assign,conf=m.pair(str(pdf),0)
            self.assertEqual(len(assign),2)
            self.assertEqual(assign['R1'][0],'10k');self.assertEqual(assign['R2'][0],'10k')
            self.assertTrue(all(v.startswith('中') for v in conf.values()))

if __name__=='__main__':unittest.main()

import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures'
WORK = ROOT / 'work/verification'
WORK.mkdir(parents=True, exist_ok=True)
STORAGE = 'https://b066d43c-99a7-4068-b036-648b538d2e8d.selstorage.ru'
notes = [('base','amber','Амбровый'), ('base','woody','Древесный'), ('base','sandalwood','Сандал'), ('heart','floral','Цветочный'), ('heart','lily-of-the-valley','Ландыш'), ('top','orange','Апельсин'), ('top','citrus','Цитрус'), ('top','bergamot','Бергамот')]
materials = []
profiles = []
registry = []
def cas(number):
    digits = str(number) + '00'
    check = sum(int(c)*(i+1) for i,c in enumerate(reversed(digits))) % 10
    return str(number)+'-00-'+str(check)

def material(pid, label, stage=None, family=None, solvent=False):
    row = {'id':'souwers:'+pid,'label':label,'name_ru':label,'name_en':label,'source':'souwers','cas':[cas(int(pid[-6:]))], 'aliases':[], 'notes':[{'base':'Базовые ноты','heart':'Ноты сердца','top':'Верхние ноты'}.get(stage,'')], 'families':[family] if family else [], 'roles':[], 'description_ru':'Тестовый материал', 'kind':'solvent' if solvent else 'aroma_chemical', 'form':{'kind':'solvent' if solvent else 'pure'}, 'ifra':{'category':'4','max_percent':100,'calculation_eligible':True,'status':'verified_certificate'}, 'allergens':{'complete':True,'items':[]}, 'shop':{'url':'https://souwers.ru/tproduct/2461077751-'+pid,'price_per_g':10,'packs':[]}, 'working_dose':{'max_percent':40,'min_percent':0.01,'material_basis':'as_sold_material','basis':'fragrance_concentrate','display_ru':'Тестовый диапазон'}}
    materials.append(row)
    registry.append({'id':pid,'enabled':True,'name_ru':label,'display_name':label,'aliases':[],'cas':row['cas'],'form':row['form'],'url':row['shop']['url'],'taxonomy':{'families_ru':row['families'],'note_positions_ru':row['notes'],'roles_ru':[]}})
    if stage:
        profiles.append({'product_id':pid,'olfactory':{'positions':[stage],'families':[{'id':family,'label':label}], 'facets':[{'id':family,'label':label}], 'title':label}})

material('177886691462','Дипропиленгликоль / DPG',solvent=True)
for index, (stage, family, label) in enumerate(notes):
    for part in range(3):
        # One crystal splits a note into two mixing runs. Folding must hide both.
        material(str(200000000000+index*100+part), label+' компонент '+str(part+1)+(' (Кристаллы)' if family=='amber' and part==2 else ''), stage, family)

catalogue = {'schema':'souwers-formulary-materials','version':'test','materials':materials,'stats':{}}
seed = '''
window.tcart={products:[]}; window.tcart_oneproduct='n'; window.nativeCalls=[]; window.cartEvents=0;
window.tcart__syncProductsObject__LStoObj=()=>{};
for(const name of ['tcart__updateTotalProductsinCartObj','tcart__saveLocalObj','tcart__reDrawProducts','tcart__reDrawTotal','tcart__reDrawCartIcon'])window[name]=()=>{};
window.tcart__addProduct=(item)=>{window.nativeCalls.push({opening:document.querySelector('.t706').getAttribute('data-opencart-onorder'),img:item.img,uid:item.uid});let row=tcart.products.find(row=>row.uid===item.uid);if(row)row.quantity++;else tcart.products.push({...item});return true;};
document.addEventListener('souwers:cart-variants-updated',()=>window.cartEvents++);
'''
html = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0;background:#f6f9f7;font-family:Arial}.site-header{height:50px;position:sticky;top:0;background:white;z-index:10}.sa-formulary-frame{display:block;width:100%;border:0}#souwers-account{padding:12px}</style><body><div class="site-header">SOUWERS · проверка конструктора</div><div class="t706" data-opencart-onorder="yes"></div><div id="souwers-account" data-section="formulary"><div id="host"></div></div>
<template id="souwers-account-formulary-template"><link rel="stylesheet" href="'''+STORAGE+'''/scripts/souwers-formulary-v2.7.0.css"><section id="souwers-formulary"></section></template>
<script id="souwers-account-formulary-config" type="application/json">{"scriptUrl":"'''+STORAGE+'''/scripts/souwers-formulary-v2.7.0.js"}</script><script>'''+seed+'''</script><script src="/account.js"></script><script>SouwersAccountFormulary.mount(document.getElementById('host'));</script></body></html>'''

product_mode = {'mode':'gallery-string', 'quantity':100}
unexpected = []
def route_handler(route):
    url = route.request.url
    parsed = urlparse(url)
    path = parsed.path
    headers = {'Access-Control-Allow-Origin':'*'}
    if url.startswith('https://souwers.ru/test'):
        return route.fulfill(body=html,content_type='text/html')
    if path.endswith('/account.js'):
        return route.fulfill(path=str(ROOT/'scripts/souwers-account-formulary-v1.0.3.js'),content_type='text/javascript')
    if path.endswith('souwers-formulary-v2.7.0.js'):
        return route.fulfill(path=str(ROOT/'scripts/souwers-formulary-v2.7.0.js'),content_type='text/javascript',headers=headers)
    if path.endswith('souwers-formulary-v2.7.0.css'):
        return route.fulfill(path=str(ROOT/'scripts/souwers-formulary-v2.7.0.css'),content_type='text/css',headers=headers)
    if path.endswith('souwers-builder-pdf-v1.0.0.js'):
        return route.fulfill(path=str(ROOT/'archive/input-2026-11-03/souwers-builder-pdf-v1.0.0.js'),content_type='text/javascript',headers=headers)
    data = None
    if 'formulary-materials-' in path or 'lab-materials-' in path: data = catalogue
    elif path.endswith('material-profiles.json'): data = {'products':profiles}
    elif path.endswith('components-registry.json'): data = {'schema':'souwers-components-registry','components':registry,'version':'test'}
    elif path.endswith('formulary-index.json'): data = {'products':[]}
    elif parsed.hostname=='store.tildaapi.com':
        pid = parse_qs(parsed.query)['productuid'][0]
        mode = product_mode['mode']
        if pid=='108130609132' and (FIXTURES/'tilda-orange.json').exists():
            return route.fulfill(path=str(FIXTURES/'tilda-orange.json'),content_type='application/json',headers=headers)
        product = {'uid':pid,'title':'Тестовый товар '+pid,'price':'200','quantity':product_mode['quantity'],'json_options':json.dumps([{'title':'Объем (вес)'}]),'editions':json.dumps([{'uid':str(int(pid)+100000),'Объем (вес)':'5 г','price':'200','quantity':product_mode['quantity']}]),'gallery':'[]','partuids':'["594843203103"]'}
        cover = 'https://static.tildacdn.com/test/cover-'+pid+'.jpg'
        if mode=='gallery-string': product['gallery']=json.dumps([cover])
        elif mode=='gallery-object': product['gallery']=json.dumps([{'img':cover}])
        elif mode=='gallery-src': product['gallery']=json.dumps([{'src':cover}])
        elif mode=='product-image': product['img']=cover
        elif mode=='gallery-second': product['gallery']=json.dumps([{}, {'img':cover}])
        elif mode=='edition-image':
            editions=json.loads(product['editions']);editions[0]['img']=cover;product['editions']=json.dumps(editions)
        elif mode=='invalid-edition':
            editions=json.loads(product['editions']);editions[0]['img']='not-an-image';product['editions']=json.dumps(editions);product['gallery']=json.dumps([{'img':cover}])
        data = {'product':product,'partuid':'594843203103'}
    if data is not None: return route.fulfill(body=json.dumps(data,ensure_ascii=False),content_type='application/json',headers=headers)
    if path.endswith('.jpg'): return route.fulfill(body='',content_type='image/jpeg',headers=headers)
    unexpected.append(url)
    return route.fulfill(status=404,body='Unmocked test request',headers=headers)

checks=[]
def check(value,label):
    if not value and 'page' in globals():
        page.screenshot(path=str(WORK/'failure.png'))
    assert value,label
    checks.append(label)
    print('PASS',label,flush=True)

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-crashpad-for-testing','--disable-crash-reporter','--no-zygote','--single-process','--disable-gpu','--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1)
    context.route('**/*',route_handler)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda error: errors.append(str(error)))
    page.goto('https://souwers.ru/test')
    iframe=page.frame_locator('.sa-formulary-frame')
    iframe.locator('[data-action="pyramid"]').wait_for()
    frame=page.frames[1]
    frame.wait_for_function('window.SouwersFormulary')
    iframe.locator('[data-action="pyramid"]').click()
    iframe.locator('#swb-builder').wait_for()
    frame.wait_for_function('!document.querySelector("[data-swb-profile-status]").textContent')
    check(iframe.locator('[data-swb-title]').input_value()=='','fresh builder title is empty')
    check(iframe.locator('.swb-name').inner_text().strip()=='Придумай название аромата','name prompt is explicit')
    art_result=frame.evaluate('''()=>{const notes=SouwersStudio.catalogue;const svgs=notes.map(note=>SouwersNoteArt.svg(note.art));return {count:notes.length,unique:new Set(svgs).size};}''')
    check(art_result['count']==art_result['unique'],'all predefined notes have distinct SVGs: '+str(art_result))
    for stage,family,label in notes:
        iframe.locator('[data-swb-note-select="'+stage+'"]').select_option(family)
    iframe.locator('[data-swb-setting="batchGrams"]').fill('100')
    iframe.locator('[data-swb-setting="strengthPercent"]').fill('30')
    iframe.locator('[data-swb-setting="resolution"]').select_option('0.01')
    check(not iframe.locator('[data-swb-action="create"]').is_disabled(),'generated composition is valid')
    check(iframe.locator('[data-swb-row]').count()>16,'components were generated through the real engine')
    frame.evaluate('window.baskets=[...document.querySelectorAll(".swb-basket")];window.rows=[...document.querySelectorAll("[data-swb-row]")];window.inputs=[...document.querySelectorAll("[data-swb-amount]")];window.order=rows.map(row=>row.dataset.swbRow)')
    total_before=iframe.locator('[data-swb-total-grams]').inner_text()
    amber=iframe.locator('[data-swb-action="toggle-note"][data-key="base|amber"]').first
    amber.click()
    check(frame.evaluate('''()=>[...document.querySelectorAll('[data-swb-row]')].filter(row=>row.dataset.swbRow.startsWith('base|amber|')).every(row=>row.hidden)'''),'folding hides every amber component across mixing runs')
    check(total_before==iframe.locator('[data-swb-total-grams]').inner_text(),'folding does not change formula totals')
    mini=iframe.locator('[data-swb-mini][data-swb-intensity="orange"]')
    frame.evaluate('document.querySelector("#swf-dialog").scrollTop=0')
    mini.focus()
    mini.press('ArrowRight')
    frame.wait_for_timeout(80)
    anchor=frame.evaluate('''()=>{const d=document.querySelector('#swf-dialog'),h=d.querySelector(':scope > header'),m=document.querySelector('.swb-sticky-mixer'),r=[...document.querySelectorAll('[data-swb-row]')].find(row=>row.dataset.swbRow.startsWith('top|orange|'));return {offset:r.getBoundingClientRect().top-d.getBoundingClientRect().top-h.getBoundingClientRect().height-m.getBoundingClientRect().height,top:d.scrollTop};}''')
    check(anchor['top']>200 and 0<=anchor['offset']<=12,'mini slider anchors the first component below the fixed controls: '+str(anchor))
    check(frame.evaluate('baskets.every((node,index)=>node===document.querySelectorAll(".swb-basket")[index])'),'basket DOM nodes survive a note slider update')
    check(frame.evaluate('inputs.every((node,index)=>node===document.querySelectorAll("[data-swb-amount]")[index])'),'component inputs survive a note slider update')
    check(frame.evaluate('order.join()==[...document.querySelectorAll("[data-swb-row]")].map(row=>row.dataset.swbRow).join()'),'collapsing and editing preserve mixing order')
    anchored_top=frame.evaluate('document.querySelector("#swf-dialog").scrollTop')
    mini.press('ArrowRight')
    check(abs(frame.evaluate('document.querySelector("#swf-dialog").scrollTop')-anchored_top)<2,'continued slider edits do not repeatedly scroll the dialog')
    iframe.locator('[data-swb-action="focus-note"][data-key="base|amber"]').click()
    frame.wait_for_timeout(450)
    check(frame.evaluate('''()=>[...document.querySelectorAll('[data-swb-row]')].filter(row=>row.dataset.swbRow.startsWith('base|amber|')).every(row=>!row.hidden)'''),'note navigation expands a previously folded note')
    check(frame.evaluate(r'''()=>[...document.querySelectorAll('.swb-weight-cell>b')].every(node=>/^\d+,\d{2}$/.test(node.textContent))'''),'weights use uniform decimal places')
    first_input=iframe.locator('[data-swb-amount]').first
    first_input.fill('1,25')
    check(first_input.input_value()=='1,25','editing a component preserves decimal input and focus')
    check(not iframe.locator('[data-swb-action="create"]').is_disabled(),'composition remains valid after a numeric edit')
    iframe.locator('[data-swb-title]').fill('Мой апельсиновый сад')
    iframe.locator('[data-swb-action="toggle-notes"]').click()
    check(frame.evaluate('''()=>[...document.querySelectorAll('[data-swb-row]')].filter(row=>!row.dataset.swbRow.startsWith('carrier|')).every(row=>row.hidden)'''),'collapse-all hides note rows and leaves solvents visible')
    iframe.locator('[data-swb-action="toggle-notes"]').click()
    check(frame.evaluate('''()=>[...document.querySelectorAll('[data-swb-row]')].every(row=>!row.hidden)'''),'expand-all restores all rows')
    for mode in ['gallery-string','gallery-object','gallery-src','product-image','gallery-second','edition-image','invalid-edition','empty']:
        product_mode['mode']=mode
        before=page.evaluate('nativeCalls.length')
        result=frame.evaluate('''async ()=>{const material=SouwersFormulary.getMaterials().find(m=>m.id==='souwers:200000000500');const result=await SouwersLabCart.add(material,1);return result.changed;}''')
        calls=page.evaluate('nativeCalls')
        check(not result and len(calls)>before and calls[-1]['img'].startswith('https://static.tildacdn.com/') if mode!='empty' else calls[-1]['img']=='','cart cover supports '+mode)
    check(page.evaluate('nativeCalls.every(call=>call.opening==="no")'),'iframe additions suppress parent cart auto-opening')
    check(page.locator('.t706').get_attribute('data-opencart-onorder')=='yes','parent cart opening setting is restored')
    check(page.evaluate('cartEvents')>=8,'variant refresh events reach the parent account document')
    if (FIXTURES/'orange-material.json').exists():
        orange=json.loads((FIXTURES/'orange-material.json').read_text())
        frame.evaluate('async material=>SouwersLabCart.add(material,1)',orange)
        check(page.evaluate('nativeCalls[nativeCalls.length-1].img.endsWith(".webp")'),'actual Orange EO API response supplies its product cover')
    baseline=page.evaluate('JSON.stringify(tcart)')
    product_mode['quantity']=0
    stock_error=frame.evaluate('''async ()=>{try{await SouwersLabCart.add(SouwersFormulary.getMaterials().find(m=>m.id==='souwers:200000000500'),1);return '';}catch(error){return error.message;}}''')
    check(bool(stock_error) and baseline==page.evaluate('JSON.stringify(tcart)'),'out-of-stock quote leaves the cart unchanged')
    product_mode['quantity']=100
    page.evaluate('()=>{window.originalAdd=tcart__addProduct;window.failedAdds=0;window.tcart__addProduct=item=>{if(++failedAdds===2)return false;return originalAdd(item)};}')
    rollback_error=frame.evaluate('''async ()=>{try{const materials=SouwersFormulary.getMaterials().filter(m=>['souwers:200000000500','souwers:200000000501'].includes(m.id));await SouwersLabCart.addMany(materials.map(material=>({material,grams:1})));return '';}catch(error){return error.message;}}''')
    check(bool(rollback_error) and baseline==page.evaluate('JSON.stringify(tcart)'),'failed bulk addition restores the original cart')
    page.evaluate('()=>{window.tcart__addProduct=window.originalAdd;}')
    product_mode['mode']='gallery-string'
    with page.expect_download() as download:
        iframe.locator('[data-swb-action="export-xlsx"]').click()
    downloaded=download.value
    downloaded.save_as(WORK/'test-export.xlsx')
    check((WORK/'test-export.xlsx').read_bytes().startswith(b'PK'),'Excel export remains downloadable')
    with page.expect_download(timeout=30000) as download:
        iframe.locator('[data-swb-action="export-pdf"]').click()
    download.value.save_as(WORK/'test-export.pdf')
    check((WORK/'test-export.pdf').read_bytes().startswith(b'%PDF'),'PDF export remains downloadable')
    # Save screenshot of the actual iframe UI at table position for visual inspection.
    frame.evaluate('document.querySelector("#swf-dialog").scrollTop=900')
    page.screenshot(path=str(WORK/'desktop.png'))
    iframe.locator('[data-swb-action="close"]').click()
    iframe.locator('[data-action="pyramid"]').click()
    check(iframe.locator('[data-swb-title]').input_value()=='Мой апельсиновый сад','custom aroma title survives reopening')
    # A fresh pointer gesture on the pinned strip must retain the actual slider node.
    mini=iframe.locator('[data-swb-mini][data-swb-intensity="orange"]')
    frame.evaluate('document.querySelector("#swf-dialog").scrollTop=0')
    mini.evaluate('node=>window.dragSlider=node')
    box=mini.bounding_box()
    page.mouse.move(box['x']+box['width']*.12,box['y']+box['height']/2)
    page.mouse.down()
    page.mouse.move(box['x']+box['width']*.16,box['y']+box['height']/2,steps=4)
    page.mouse.up()
    check(frame.evaluate('dragSlider===document.querySelector("[data-swb-mini][data-swb-intensity=orange]") && dragSlider.isConnected'),'pointer drag keeps the same pinned slider node')
    page.set_viewport_size({'width':390,'height':844})
    frame.wait_for_timeout(150)
    mobile_overflow=frame.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    check(not mobile_overflow,'mobile account iframe has no horizontal page overflow')
    mini=iframe.locator('[data-swb-mini][data-swb-intensity="orange"]')
    # Bring the desired mini card into view only inside its own horizontal strip.
    mini.evaluate('node=>node.parentElement.parentElement.scrollLeft=node.parentElement.offsetLeft')
    mini.focus()
    mini.press('ArrowRight')
    frame.wait_for_timeout(100)
    page.screenshot(path=str(WORK/'mobile.png'))
    check(not errors,'no browser exceptions: '+repr(errors))
    check(not unexpected,'no unexpected network requests: '+repr(unexpected))
    browser.close()

(WORK/'verification.json').write_text(json.dumps({'checks':checks,'browser_errors':errors,'unexpected_requests':unexpected},ensure_ascii=False,indent=2))
print('TOTAL',len(checks),'checks',flush=True)

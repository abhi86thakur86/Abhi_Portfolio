// Rebuilding requires @oai/artifact-tool in the Node module resolution path.
// In ChatGPT's authoring runtime use CODEX_PRIMARY_RUNTIME_NODE and its bundled
// node_modules via a temporary working-directory symlink. On other systems use
// an environment where that package is available. Opening the XLSX needs only Excel.
// Usage: node build_workbook.mjs /absolute/path/to/Abhi_Portfolio
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const repo=process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const project=path.join(repo,'projects/03-hospitality-profitability');
const inputs=JSON.parse(await fs.readFile(path.join(project,'data/workbook_inputs.json'),'utf8'));
const expected=JSON.parse(await fs.readFile(path.join(project,'outputs/expected_metrics.json'),'utf8'));
const wb=Workbook.create();
const summary=wb.worksheets.add('Monthly results');
const detail=wb.worksheets.add('Sales calculation');
const source=wb.worksheets.add('Inputs');
const ink='#0F172A',navy='#1E3A5F',teal='#0F766E',muted='#64748B';
const money='"$"#,##0;("$"#,##0);"-"';
for(const s of [summary,detail,source]){
  s.showGridLines=false;
  s.getRange('A1:P165').format.font={name:'Arial',size:10,color:ink};
  s.getRange('A1:P165').format.rowHeight=22;
  s.getRange('A1:P165').format.columnWidth=15;
  s.getRange('A1:P165').format.verticalAlignment='center';
}
function heading(s,range){
  s.getRange(range).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:36};
}
source.getRange('A1:G1').values=[['Month','Channel','Category','Units','Unit price','Unit food cost','Fee rate']];
source.getRange('A2:G145').values=inputs.sales.map(r=>[new Date(r.month+'T00:00:00Z'),r.channel,r.category,r.units,r.unit_price,r.unit_food_cost,r.fee_rate]);
source.getRange('A2:A145').setNumberFormat('mmm-yy');
source.getRange('D2:F145').format.font.color='#0000FF';
source.getRange('G2:G145').format.font.color='#0000FF';
source.getRange('E2:F145').setNumberFormat('"$"0.00');
source.getRange('G2:G145').setNumberFormat('0.0%');
source.getRange('D2:G145').format.fill='#FFF7DB';
source.getRange('I1:J13').values=[['Month','Overhead (NZD)'],...inputs.overheads.map(r=>[new Date(r.month+'T00:00:00Z'),r.overhead])];
source.getRange('I2:I13').setNumberFormat('mmm-yy');
source.getRange('J2:J13').setNumberFormat(money);
source.getRange('J2:J13').format.font.color='#0000FF';
source.getRange('J2:J13').format.fill='#FFF7DB';
source.getRange('L2').values=[['Synthetic CY2025 inputs. NZD, GST exclusive.']];
source.getRange('L4').values=[['Source: scripts/build_portfolio.py, fixed random seed 42.']];
source.getRange('L6').values=[['Blue/amber cells are editable numeric inputs.']];
source.getRange('L8').values=[['Overhead includes assumed wages, rent, utilities and other opex.']];
source.getRange('L10').values=[['Rates are illustrative, not supplier quotes.']];
source.getRange('B:C').format.columnWidth=18;
source.getRange('I:J').format.columnWidth=19;
heading(source,'A1:G1');heading(source,'I1:J1');
source.freezePanes.freezeRows(1);
source.tables.add('A1:G145',true,'SalesInputs');
source.tables.add('I1:J13',true,'OverheadInputs');
source.getRange('D2:D145').dataValidation={rule:{type:'whole',operator:'greaterThanOrEqual',formula1:0}};
source.getRange('G2:G145').dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:1}};

detail.getRange('A1:J1').values=[['Month','Channel','Category','Revenue','Food cost','Channel fee','Gross profit','Contribution','Margin','Units']];
detail.getRange('A2:J145').formulas=inputs.sales.map((_,i)=>{const r=i+2;return[
 `=Inputs!A${r}`,`=Inputs!B${r}`,`=Inputs!C${r}`,`=ROUND(Inputs!D${r}*Inputs!E${r},2)`,
 `=ROUND(Inputs!D${r}*Inputs!F${r},2)`,`=ROUND(D${r}*ROUND(Inputs!G${r}*10000,0)/100,0)/100`,
 `=D${r}-E${r}`,`=G${r}-F${r}`,`=IF(D${r}=0,"n.a.",H${r}/D${r})`,`=Inputs!D${r}`];});
detail.getRange('A2:A145').setNumberFormat('mmm-yy');
detail.getRange('D2:H145').setNumberFormat(money);
detail.getRange('I2:I145').setNumberFormat('0.0%');
detail.getRange('A2:E145').format.font.color='#008000';
detail.getRange('J2:J145').format.font.color='#008000';
detail.getRange('B:C').format.columnWidth=18;
heading(detail,'A1:J1');detail.freezePanes.freezeRows(1);
detail.tables.add('A1:J145',true,'SalesCalculation');

summary.tabColor=navy;
summary.getRange('A2').values=[['Hospitality profitability']];
summary.getRange('A2').format.font={size:16,bold:true,color:navy};
summary.getRange('A3').values=[['Synthetic CY2025. NZD, GST exclusive.']];
summary.getRange('A3').format.font={italic:true,color:muted};
summary.getRange('A5:B8').values=[['Annual measure','NZD'],['Revenue',null],['Contribution',null],['Operating surplus',null]];
summary.getRange('B6:B8').formulas=[['=SUM(B13:B24)'],['=SUM(F13:F24)'],['=SUM(I13:I24)']];
summary.getRange('B6:B8').setNumberFormat(money);
summary.getRange('A5:B5').format.font.bold=true;
summary.getRange('A6:A8').format.columnWidth=23;
summary.getRange('D6').values=[['Contribution = revenue less food cost and channel fees.']];
summary.getRange('D7').values=[['Operating surplus = contribution less assumed overhead.']];
summary.getRange('D8').values=[['Excludes owner pay, interest, depreciation and income tax.']];
summary.getRange('D9').values=[['Operating surplus is not cash flow or owner take-home pay.']];
summary.getRange('A12:I12').values=[['Month','Revenue','Food cost','Channel fees','Gross profit','Contribution','Margin','Overhead','Operating surplus']];
summary.getRange('A13:I24').formulas=inputs.overheads.map((_,i)=>{const r=i+13,s=i+2;return[
 `=Inputs!I${s}`,
 `=SUMIFS('Sales calculation'!$D$2:$D$145,'Sales calculation'!$A$2:$A$145,A${r})`,
 `=SUMIFS('Sales calculation'!$E$2:$E$145,'Sales calculation'!$A$2:$A$145,A${r})`,
 `=SUMIFS('Sales calculation'!$F$2:$F$145,'Sales calculation'!$A$2:$A$145,A${r})`,
 `=SUMIFS('Sales calculation'!$G$2:$G$145,'Sales calculation'!$A$2:$A$145,A${r})`,
 `=SUMIFS('Sales calculation'!$H$2:$H$145,'Sales calculation'!$A$2:$A$145,A${r})`,
 `=IF(B${r}=0,"n.a.",F${r}/B${r})`,`=Inputs!J${s}`,`=F${r}-H${r}`];});
summary.getRange('A13:A24').setNumberFormat('mmm-yy');
summary.getRange('B13:I25').setNumberFormat(money);
summary.getRange('G13:G25').setNumberFormat('0.0%');
summary.getRange('G13:G25').format.font.italic=true;
summary.getRange('A25').values=[['Total']];
for(const c of ['B','C','D','E','F','H','I'])summary.getRange(`${c}25`).formulas=[[`=SUM(${c}13:${c}24)`]];
summary.getRange('G25').formulas=[['=IF(B25=0,"n.a.",F25/B25)']];
summary.getRange('A25:I25').format.font.bold=true;
summary.getRange('A25:I25').format.borders={preset:'doubleBottom',style:'thin',color:navy};
heading(summary,'A12:I12');
summary.getRange('I12:I25').format.columnWidth=19;
summary.getRange('I13:I24').conditionalFormats.add('cellIs',{operator:'lessThan',formula:0,format:{fill:'#FEE2E2',font:{color:'#991B1B'}}});

summary.getRange('K12:M12').values=[['Channel','Revenue','Contribution']];
summary.getRange('K13:K15').values=[['Dine-in'],['Pickup'],['Delivery']];
for(let r=13;r<=15;r++)summary.getRange(`L${r}:M${r}`).formulas=[[
 `=SUMIFS('Sales calculation'!$D$2:$D$145,'Sales calculation'!$B$2:$B$145,K${r})`,
 `=SUMIFS('Sales calculation'!$H$2:$H$145,'Sales calculation'!$B$2:$B$145,K${r})`]];
summary.getRange('L13:M15').setNumberFormat(money);heading(summary,'K12:M12');
summary.getRange('K18').values=[['Interpretation: outputs/findings.md']];
summary.getRange('K20').values=[['Loss follows assumed costs and volume.']];
summary.getRange('K22').values=[['Try changing one overhead input.']];

// Chart uses linked month labels to avoid date serials in the preview engine.
summary.getRange('K27:M27').values=[['Month','Contribution','Overhead']];
summary.getRange('K28:M39').formulas=inputs.overheads.map((_,i)=>[
 `=TEXT(A${i+13},"mmm")`,`=F${i+13}`,`=H${i+13}`]);
const chart=summary.charts.add('line',summary.getRange('K27:M39'));
chart.title='Monthly contribution and overhead (NZD)';
chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=12;
chart.setPosition('A28','I43');
chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};
chart.yAxis={numberFormatCode:'$0,"k"',numberFormatSourceLinked:false,textStyle:{typeface:'Arial'}};
chart.legend={position:'top',textStyle:{typeface:'Arial'}};
chart.series.items[0].line={fill:teal,style:'solid',width:2};
chart.series.items[1].line={fill:'#D97706',style:'dashed',width:2};

wb.recalculate();
// Compare independently computed SQLite controls with recalculated workbook values.
const close=(actual,target,label)=>{if(typeof actual!=='number'||Math.abs(actual-target)>.011)throw new Error(`${label}: ${actual} != ${target}`);};
close(summary.getRange('B25').values[0][0],expected.revenue,'Annual revenue');
close(summary.getRange('F25').values[0][0],expected.contribution,'Annual contribution');
close(summary.getRange('I25').values[0][0],expected.operating_surplus,'Annual operating surplus');
// A changed input must propagate to detail, monthly summary and annual totals.
const initial=source.getRange('D2').values[0][0];
const before=summary.getRange('B25').values[0][0];
source.getRange('D2').values=[[initial+10]];
wb.recalculate();
close(summary.getRange('B25').values[0][0],before+10*inputs.sales[0].unit_price,'Volume sensitivity');
source.getRange('D2').values=[[0]];wb.recalculate();
if(detail.getRange('I2').values[0][0]!=='n.a.')throw new Error('Zero revenue margin must be n.a.');
source.getRange('D2').values=[[initial]];wb.recalculate();
close(summary.getRange('B25').values[0][0],expected.revenue,'Restored revenue');
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:20},summary:'Formula error scan'})).ndjson);
console.log((await wb.inspect({kind:'table',range:"'Monthly results'!A25:I25",include:'values,formulas',tableMaxRows:2,tableMaxCols:9,maxChars:2000})).ndjson);
for(const [s,range,file] of [[summary,'A1:M44','workbook-preview.png'],[detail,'A1:J12','calculation-preview.png'],[source,'A1:P14','inputs-preview.png']]){
 const png=await wb.render({sheetName:s.name,range,scale:1.3,format:'png'});
 await fs.writeFile(path.join(process.env.PORTFOLIO_PREVIEW_DIR || path.join(project,'outputs'),file),new Uint8Array(await png.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(project,'hospitality_analysis.xlsx'));
console.log('PASS: workbook totals match SQLite; input change and zero-revenue checks passed.');

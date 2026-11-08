"""为现有逐页资料生成可追溯主题目录；只负责定位，不宣称逐页审核。"""
import csv, pathlib, sqlite3
ROOT=pathlib.Path(__file__).resolve().parents[1]/'knowledge'/'六份资料索引'
TOPICS={
'柜型与结构':['GGD','MNS','抽屉柜','固定式','隔室'],
'母排与接地':['母线','母排','接地','保护导体','等电位'],
'断路器选型':['断路器','分断能力','脱扣器','短路保护'],
'短路和选择性':['短路电流','短时耐受','选择性','短路计算'],
'接触器与继电器':['接触器','热继电器','中间继电器','触头'],
'软启动与旁路':['软起动','软启动','旁路接触器','限流起动'],
'变频调速':['变频器','变频调速','变频器参数','电抗器'],
'电机与机械负载':['异步电动机','负载转矩','飞轮矩','机械特性','电动机'],
'控制与联锁':['互锁','自锁','电气控制','多地控制','控制回路'],
'无功补偿':['无功补偿','电容补偿','功率因数','电容器'],
'成套验证':['设计验证','例行检验','温升','介电性能','机械操作'],
'标准条款':['范围','规范性引用','保护电路','电气间隙','爬电距离'],
}
def main():
    db=sqlite3.connect(ROOT/'pages.sqlite3'); out=ROOT/'主题页码线索.csv'
    with out.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f); writer.writerow(['主题','资料','PDF页码','匹配词','来源','状态'])
        for b,p,src,text in db.execute('select book,page,source,text from pages order by book,page,source'):
            for topic,words in TOPICS.items():
                found=[x for x in words if x in text]
                if found: writer.writerow([topic,b,p,'、'.join(found),src,'自动线索，未逐项审核'])
    print('输出：',out)
if __name__=='__main__':main()

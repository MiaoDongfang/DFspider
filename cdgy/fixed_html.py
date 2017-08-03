#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library

from bs4 import BeautifulSoup
from lxml import html

__author__ = "dong fang"

html_str = """
  <td align="center" colspan="4" height="250" valign="top">
   <table border="0" cellpadding="0" cellspacing="0" height="237" width="850">
    <tr>
     <td align="center" class="title1" height="35" id="myTitle" style="font-size:16px">
      关于第六批东莞市公共服务项目资助计划的公示
     </td>
    </tr>
    <tr>
     <td align="center" height="23" id="myTitle" style="font-size:13px">
      2017-05-27
      <br/>
     </td>
    </tr>
    <tr>
     <td class="text3" height="145" id="myContent" style="font-size:14px" valign="top">
      <div>
       <br/>
       根据《关于实施创新驱动发展战略 开展智能制造和服务型制造示范工程加快推动工业转型升级的意见》（东府〔
       <span>
        2015〕30号）以及《市经信局公共服务项目资助实施细则（试行）》等相关文件要求，经过项目网上备案、活动现场核查、项目网上申报、材料形式审查、市科协专家评审、征求意见、资金投入核查等工作流程，现将《第六批东莞市公共服务项目资助计划》（详见附件）予以公示。
       </span>
      </div>
      <div>
       公示期间，如有异议，请以书面方式向市经济和信息化局法规科反映。以个人名义反映情况的，请提供真实姓名、联系方式、反映的具体事项以及相关的证明材料；以单位名义反映情况的，请提供单位真实名称（加盖公章）、联系人、联系方式、反映的具体事项以及相关的证明材料。
      </div>
      <div>
       公示期间：
       <span>
        2017年5月26日至2016年6月2日
       </span>
      </div>
      <div>
       受理单位：市经济和信息化局法规科
      </div>
      <div>
       地址：南城区鸿福西路
       <span>
        68号塞纳嘉园二楼
       </span>
      </div>
      <div>
       电话：
       <span>
        0769-22226290
       </span>
      </div>
      <div>
       传真：
       <span>
        0769-22226290
       </span>
      </div>
      <div>
      </div>
      <div align="right">
       东莞市经济和信息化局
      </div>
      <div align="right">
       2017年
       <span>
        5月26日
       </span>
      </div>
      <div align="left">
      </div>
      <div align="left">
      </div>
      <table border="0" cellpadding="0" cellspacing="0" width="100">
       <tr>
        <td height="15">
        </td>
       </tr>
      </table>
     </td>
    </tr>
   </table>
   <table align="center" border="0" cellpadding="0" cellspacing="0" height="1" width="96%">
    <tr>
     <td align="left" id="qw" style="font-size:14">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%">
       <tr>
        <td height="10">
        </td>
       </tr>
      </table>
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%">
       <tr>
        <td background="../images/twswjImg/line.gif" height="1">
        </td>
       </tr>
      </table>
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%">
       <tr>
        <td height="18">
         附件列表：
        </td>
       </tr>
      </table>
      <table cellspacing="0" id="NewsView_Content1_dlFileList" style="border-collapse:collapse;">
       <tr>
        <td>
         <table border="0" cellpadding="0" cellspacing="0" width="100%">
          <tr>
          </tr>
          <tr>
           <td>
           </td>
           <td>
            <table border="0" cellpadding="0" cellspacing="0" height="35px">
             <tr width="10">
              <td align="center" style="cursor: hand">
               <img id="NewsView_Content1_dlFileList_myimg_0" src="http://dgetb.dg.gov.cn/dgetbWebLib/Images/DocImg/TXT.gif" title="关于第六批东莞市公共服务项目资助计划的公示"/>
              </td>
              <td valign="middle">
               <span onclick="OpenFiles('8508')" style="cursor: hand">
                关于第六批东莞市公共服务项目资助计划的公示
               </span>
              </td>
              <td width="5">
              </td>
             </tr>
             <tr style="display: none" width="10">
              <td align="center">
               <span class="text" id="NewsView_Content1_dlFileList_lblTitle_0" style="color:Red;">
               </span>
              </td>
             </tr>
            </table>
           </td>
          </tr>
          <tr>
           <td>
           </td>
          </tr>
         </table>
        </td>
       </tr>
      </table>
     </td>
    </tr>
   </table>
   <table border="0" width="100">
    <tr>
     <td height="20">
     </td>
    </tr>
   </table>
  </td>
 """

soup = BeautifulSoup(html_str, "lxml")
html_str = soup.prettify()

tree = html.fromstring(html_str)
print(tree.xpath("//table[@id='NewsView_Content1_dlFileList']//tr/td/table//tr/td[2]/table//tr[1]/td[2]/span/text()"))

# print(html_str.replace("<html>", "").replace("</html>", "").replace("<body>", "").replace("</body>", ""))

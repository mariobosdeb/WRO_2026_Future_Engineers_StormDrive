// Planificator lattice (A*) pentru Obstacle: cale cu inainte/inapoi printre pereti + stalpi, cu regula culorilor.
// Cadrul terenului: [0,3]^2, perete interior [1,2]^2.
#include <bits/stdc++.h>
using namespace std;
static const double S=3.0;
namespace {
struct Pil{double x,y;int col;double ax,ay;};
struct Ctx{
  vector<Pil> pil;
  double CW=0.18,FR=0.21,BK=0.04;
  double MW=0.03,MP=0.035,EXTRA=0.02,WLO=-0.24,WHI=0.07;
  vector<float> wdist; double WR=0.01; int NW=0;
  vector<pair<double,double>> per;
  const float *Pt,*Ut,*Ht; int NT; double TR;
} C;
double seg_d(double px,double py,double x0,double y0,double x1,double y1){double dx=x1-x0,dy=y1-y0;double t=((px-x0)*dx+(py-y0)*dy)/(dx*dx+dy*dy+1e-12);t=max(0.0,min(1.0,t));return hypot(px-(x0+t*dx),py-(y0+t*dy));}
double wall_exact(double px,double py){
  static const double W[8][4]={{0,0,S,0},{S,0,S,S},{S,S,0,S},{0,S,0,0},{1,1,2,1},{2,1,2,2},{2,2,1,2},{1,2,1,1}};
  double m=1e9;for(int i=0;i<8;i++)m=min(m,seg_d(px,py,W[i][0],W[i][1],W[i][2],W[i][3]));return m;}
inline double wall_d(double px,double py){
  if(px<0||py<0||px>S||py>S) return -1;
  int i=(int)lround(px/C.WR),j=(int)lround(py/C.WR); if(i<0||j<0||i>=C.NW||j>=C.NW) return -1; return C.wdist[(size_t)i*C.NW+j];}
void build_per(){C.per.clear();double hw=C.CW/2;int n=int((C.FR+C.BK)/0.025)+1;for(int i=0;i<=n;i++){double x=-C.BK+(C.FR+C.BK)*i/n;C.per.push_back({x,hw});C.per.push_back({x,-hw});}
  int m=int(C.CW/0.025)+1;for(int i=1;i<m;i++){double y=-hw+C.CW*i/m;C.per.push_back({C.FR,y});C.per.push_back({-C.BK,y});}}
inline double wrapa(double a){return a-2*M_PI*floor((a+M_PI)/(2*M_PI));}
double box_d(double dx,double dy,double th){
  double c=cos(th),s=sin(th);double lx=dx*c+dy*s,ly=-dx*s+dy*c;
  double cx=(C.FR-C.BK)/2,hl=(C.FR+C.BK)/2,hw=C.CW/2;double ax=fabs(lx-cx)-hl,ay=fabs(ly)-hw;
  double ox=max(ax,0.0),oy=max(ay,0.0);return hypot(ox,oy)+min(max(ax,ay),0.0);}
double state_clear(double x,double y,double th){
  // masina acoperita de 4 discuri de raza 0.095 (conservativ ~0.5 cm)
  static const double DX[4]={-0.0087,0.0537,0.1163,0.1787};static const double DR=0.095;
  double c=cos(th),s=sin(th);double dmin=1e9;
  double cx[4],cy[4];
  for(int i=0;i<4;i++){cx[i]=x+DX[i]*c;cy[i]=y+DX[i]*s;
    double d=wall_d(cx[i],cy[i]);if(d<0)return -1e9;d-=DR;dmin=min(dmin,d);if(dmin<C.MW)return -1e9;}
  for(auto&p:C.pil){double dx=p.x-x,dy=p.y-y; if(dx*dx+dy*dy>1.0) continue;
    double dm=1e9;for(int i=0;i<4;i++)dm=min(dm,hypot(p.x-cx[i],p.y-cy[i]));
    double d=dm-DR-0.0354;
    if(d<C.MP) return -1e9; dmin=min(dmin,d);
    double rx=x-p.x,ry=y-p.y;double sp=rx*p.ax+ry*p.ay,up=-rx*p.ay+ry*p.ax;
    if(sp>C.WLO&&sp<C.WHI&&fabs(up)<0.62){double need=C.CW/2+0.025+C.EXTRA; if(p.col==0){ if(up>-need) return -1e9;} else { if(up<need) return -1e9;}}
  }
  return dmin;}
inline void look(double x,double y,double&P,double&U,double&H){
  int i=(int)lround(x/C.TR),j=(int)lround(y/C.TR);i=max(0,min(C.NT-1,i));j=max(0,min(C.NT-1,j));
  size_t k=(size_t)i*C.NT+j;P=C.Pt[k];U=C.Ut[k];H=C.Ht[k];}
struct Node{float x,y,th;float g;int par;char gear;float P;float run;float adv;float k;};
static const float MINRUN=0.20f;
static double KDK=0.12;
}
static double HW=1.0;
extern "C" void set_hw(double w){HW=w;}
extern "C" void set_kdk(double w){KDK=w;}
extern "C" int plan_path(
  int n_pil,const double*pil,
  double x0,double y0,double th0,int gear0,
  const float*Pt,const float*Ut,const float*Ht,int NT,double TR,double Ptotal,
  double dP,double umax,double hmax,
  double kmax,double ds,
  double mw,double mp,double extra,double wlo,double whi,
  int allow_rev,double revc,double gearc,
  double k_clear,double k_u,double k_h,
  int use_rect,double rx0,double ry0,double rx1,double ry1,
  int maxexp,double*out,int maxout,int*n_out,double*cost_out,int*expanded_out){
  C.pil.clear();for(int i=0;i<n_pil;i++)C.pil.push_back({pil[5*i],pil[5*i+1],(int)lround(pil[5*i+2]),pil[5*i+3],pil[5*i+4]});
  C.MW=mw;C.MP=mp;C.EXTRA=extra;C.WLO=wlo;C.WHI=whi;C.Pt=Pt;C.Ut=Ut;C.Ht=Ht;C.NT=NT;C.TR=TR;
  static bool init=false;
  if(!init){build_per();C.NW=(int)lround(S/C.WR)+1;C.wdist.assign((size_t)C.NW*C.NW,0);for(int i=0;i<C.NW;i++)for(int j=0;j<C.NW;j++)C.wdist[(size_t)i*C.NW+j]=wall_exact(i*C.WR,j*C.WR);init=true;}
  const double RES=0.02;const int NTH=72;int NX=(int)lround(S/RES)+1;
  vector<char> vis((size_t)2*NX*NX*NTH,0);
  auto key=[&](double x,double y,double th,int g){int ix=(int)lround(x/RES),iy=(int)lround(y/RES);double t=fmod(th,2*M_PI);if(t<0)t+=2*M_PI;int it=(int)floor(t/(2*M_PI)*NTH)%NTH;return (((size_t)g*NX+ix)*NX+iy)*NTH+it;};
  double c0; { double mw_=C.MW,mp_=C.MP; C.MW=-1e3; C.MP=-1e3; c0=state_clear(x0,y0,th0); C.MW=mw_; C.MP=mp_;
    if(c0>-1e8 && c0<min(C.MW,C.MP)){ C.MW=min(C.MW,c0-0.002); C.MP=min(C.MP,c0-0.002); } }
  if(c0<-1e8){*n_out=0;*expanded_out=0;return -1;}   // start invalid
  double P0,U0,H0;look(x0,y0,P0,U0,H0);
  // ---- euristica 2D (Dijkstra pe grila de 4 cm, obstacole umflate cu semilatimea masinii)
  const double HR=0.04;const int HN=(int)lround(S/HR)+1;
  vector<float> hg((size_t)HN*HN,1e9f);
  {
    vector<char> fr((size_t)HN*HN,0);
    double infl_w=C.CW/2+0.5*C.MW, infl_p=C.CW/2+0.0354+0.5*C.MP;
    for(int i=0;i<HN;i++)for(int j=0;j<HN;j++){double x=i*HR,y=j*HR;bool ok=true;
      double wd=wall_exact(x,y); if(x<0.0||y<0.0||x>S||y>S||wd<infl_w) ok=false;
      if(ok)for(auto&p:C.pil){if(hypot(p.x-x,p.y-y)<infl_p){ok=false;break;}}
      fr[(size_t)i*HN+j]=ok;}
    typedef pair<float,int> HI;priority_queue<HI,vector<HI>,greater<HI>> hq;
    for(int i=0;i<HN;i++)for(int j=0;j<HN;j++){size_t k=(size_t)i*HN+j;if(!fr[k])continue;double Pg,Ug,Hg;look(i*HR,j*HR,Pg,Ug,Hg);
      double adv=fmod(Pg-P0+2*Ptotal,Ptotal);
      bool g=(adv>=dP&&adv<dP+1.0&&fabs(Ug)<umax);
      if(g&&use_rect){double x=i*HR,y=j*HR;if(x<rx0||x>rx1||y<ry0||y>ry1)g=false;}
      if(g){hg[k]=0;hq.push({0,(int)k});}}
    while(!hq.empty()){auto [d,k]=hq.top();hq.pop();if(d>hg[k])continue;int i=k/HN,j=k%HN;
      for(int di=-1;di<=1;di++)for(int dj=-1;dj<=1;dj++){if(!di&&!dj)continue;int a=i+di,b=j+dj;if(a<0||b<0||a>=HN||b>=HN)continue;size_t kk=(size_t)a*HN+b;if(!fr[kk])continue;
        float nd=d+(float)(HR*((di&&dj)?1.4142:1.0));if(nd<hg[kk]){hg[kk]=nd;hq.push({nd,(int)kk});}}}
  }
  auto hval=[&](double x,double y){int i=(int)lround(x/HR),j=(int)lround(y/HR);i=max(0,min(HN-1,i));j=max(0,min(HN-1,j));float v=hg[(size_t)i*HN+j];return v>=1e8f?(float)(dP+2.0):v;};
  vector<Node> nodes;nodes.reserve(400000);
  typedef pair<float,int> PI;priority_queue<PI,vector<PI>,greater<PI>> pq;
  nodes.push_back({(float)x0,(float)y0,(float)th0,0,-1,(char)gear0,(float)P0,MINRUN,0.0f,0.0f});
  auto heur=[&](double P){double adv=fmod(P-P0+2*Ptotal,Ptotal);if(adv>0.5*Ptotal)adv-=Ptotal; return max(0.0,dP-adv);};
  pq.push({(float)(HW*hval(x0,y0)),0});vis[key(x0,y0,th0,gear0)]=1;
  int nk=17;vector<double> ks;for(int i=0;i<nk;i++)ks.push_back(kmax*(-1.0+2.0*i/(nk-1)));
  int goal=-1;int expd=0;
  while(!pq.empty()){auto [f,id]=pq.top();pq.pop();Node n=nodes[id];expd++;if(expd>maxexp)break;
    double P,U,H;look(n.x,n.y,P,U,H);
    double adv=n.adv;
    bool ok_goal=(adv>=dP&&adv<dP+1.0&&fabs(U)<umax);
    if(ok_goal){double dh=wrapa(n.th-H);if(fabs(dh)>hmax)ok_goal=false;}
    if(ok_goal&&use_rect){double c=cos(n.th),s=sin(n.th);double hw=C.CW/2;double cx[4]={C.FR,C.FR,-C.BK,-C.BK},cy[4]={hw,-hw,hw,-hw};
      for(int i=0;i<4;i++){double px=n.x+cx[i]*c-cy[i]*s,py=n.y+cx[i]*s+cy[i]*c;if(px<rx0||px>rx1||py<ry0||py>ry1)ok_goal=false;}}
    if(ok_goal&&n.gear==0){goal=id;break;}
    for(int gsel=0;gsel<=(allow_rev?1:0);gsel++){ if(gsel!=n.gear&&n.run<MINRUN-1e-6) continue; for(double k:ks){
      double x=n.x,y=n.y,th=n.th;double dmin=1e9;
      int steps=max(1,(int)lround(ds/0.025));double h=ds/steps;double sg=gsel?-1.0:1.0;
      double xs[4],ys[4],ts[4];
      for(int s=0;s<steps;s++){double dth=sg*k*h;double tm=th+0.5*dth;x+=sg*h*cos(tm);y+=sg*h*sin(tm);th+=dth;xs[s]=x;ys[s]=y;ts[s]=th;}
      size_t kk=key(x,y,th,gsel);if(vis[kk])continue;
      bool ok=true;
      for(int s=0;s<steps&&ok;s++){double c=state_clear(xs[s],ys[s],ts[s]);if(c<-1e8)ok=false;else dmin=min(dmin,c);}
      if(!ok)continue;
      vis[kk]=1;
      double Pn,Un,Hn;look(x,y,Pn,Un,Hn);
      double dh=wrapa(th-Hn);
      double cost=ds*(1.0+k_clear*max(0.0,0.12-dmin)+k_u*fabs(Un)+k_h*fabs(dh))+0.002*fabs(k)+KDK*fabs(k-n.k)/kmax;
      if(gsel)cost*=revc; if(gsel!=n.gear)cost+=gearc;
      nodes.push_back({(float)x,(float)y,(float)th,(float)(n.g+cost),id,(char)gsel,(float)Pn,(float)(gsel==n.gear?n.run+ds:ds),(float)(n.adv+(fmod(Pn-n.P+1.5*Ptotal,Ptotal)-0.5*Ptotal)),(float)k});
      pq.push({(float)(n.g+cost+HW*hval(x,y)),(int)nodes.size()-1});
    }}
  }
  *expanded_out=expd;
  if(goal<0){*n_out=0;return 0;}
  vector<int> path;for(int i=goal;i>=0;i=nodes[i].par)path.push_back(i);reverse(path.begin(),path.end());
  int m=min((int)path.size(),maxout);
  for(int i=0;i<m;i++){const Node&q=nodes[path[i]];out[4*i]=q.x;out[4*i+1]=q.y;out[4*i+2]=q.th;out[4*i+3]=q.gear;}
  *n_out=m;*cost_out=nodes[goal].g;return 1;}


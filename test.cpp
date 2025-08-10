#include <bits/stdc++.h>
#pragma GCC optimize("Ofast")
#pragma GCC target("sse3","sse2","sse")
#pragma GCC target("avx","sse4","sse4.1","sse4.2","ssse3")
#pragma GCC target("f16c")
#pragma GCC optimize("inline","fast-math","unroll-loops","no-stack-protector")
#pragma GCC diagnostic error "-fwhole-program"
#pragma GCC diagnostic error "-fcse-skip-blocks"
#pragma GCC diagnostic error "-funsafe-loop-optimizations"
#pragma GCC diagnostic error "-std=c++14"
using namespace std;
bool check(int x){
    string a = to_string(x);
    for (char i:a){
        if(i!='8'&&i!='5')
        return false;
    }
    return true;
}
int main(){
    cout << "int a[]={";
    int hist=5;
    for(int x=1;x<=305;x++){
        int cnt=0;
        for (int i=hist;;i++){
            cout << "
            if(check(i))
                cnt++;
            if(cnt==x){
                cout << i << ",";
                hist=i+1;
                cout << flush;
                break;
            }
        }
    }
    cout << "\r];";
    return 0;
}
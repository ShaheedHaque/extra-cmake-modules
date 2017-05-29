//
// Copyright 2017 by Shaheed Haque (srhaque@theiet.org)
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions
// are met:
//
// 1. Redistributions of source code must retain the copyright
//    notice, this list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
// 3. The name of the author may not be used to endorse or promote products
//    derived from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
// IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
// OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
// NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
// THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//

#ifndef SAMPLE1_H
#define SAMPLE1_H

class QString
{
public:
    QString() {};
};

/**
 * https://www.riverbankcomputing.com/pipermail/pyqt/2017-May/039159.html
 */
class Sample1_1
{
public:
    bool simple(const char *&scursor, const char* send, QString &result, bool allow8Bit = false)
    {
        scursor = send;
        result = QString();
        return allow8Bit;
    }

    bool markedInOut(const char *&scursor, const char* send, QString &result, bool allow8Bit = false)
    {
        return simple(scursor, send, result, allow8Bit);
    }

    bool markedInOutCxxDecl(const char *&scursor, const char* send, QString &result, bool allow8Bit = false)
    {
        return markedInOut(scursor, send, result, allow8Bit);
    }
};

/**
 * https://www.riverbankcomputing.com/pipermail/pyqt/2017-May/039219.html
 */

template<typename T, T, int U>
class MyTemplate
{
    int x;
public:
    MyTemplate() { x = U; };
    T *fn() { return nullptr; };
};

namespace OuterNamespace
{
    template<typename T, int U, T>
    class MyTemplate
    {
    public:
        MyTemplate() {};
        T *fn() { return nullptr; };
    };
};

class OuterClass
{
public:
    template<typename T, int U, T Z>
    class MyTemplate
    {
    public:
        MyTemplate() {};
        T fn() { return Z; };
    };
};

#endif
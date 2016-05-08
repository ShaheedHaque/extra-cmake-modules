
#include "cpplib.h"

MyObject::MyObject(QObject* parent)
  : QObject(parent)
{

}

int MyObject::addThree(int input) const
{
  return input + 3;
}

QList<int> MyObject::addThree(QList<int> input) const
{
  auto output = input;
  std::transform(output.begin(), output.end(),
      output.begin(),
      [](int in) { return in + 3; });
  return output;
}

QString MyObject::addThree(const QString& input, const QString& prefix) const
{
  return prefix + input + QStringLiteral("Three");
}

int MyObject::findNeedle(QStringList list, QString needle, Qt::MatchFlags flags) const
{
  if (flags & Qt::MatchStartsWith) {
    auto it = std::find_if(list.begin(), list.end(), [needle](QString cand) {
      return cand.startsWith(needle);
    });
    if (it != list.end()) {
      return std::distance(list.begin(), it);
    }
    return -1;
  }
  return list.indexOf(needle);
}

int MyObject::qtEnumTest(QFlags<Qt::MatchFlag> flags)
{

}

int MyObject::localEnumTest(QFlags<LocalEnum> flags)
{

}

int MyObject::functionParam(std::function<int()> fn)
{
  return fn();
}

int MyObject::groups(unsigned int maxCount) const
{
  return maxCount;
}

class FwdDecl
{

};

int MyObject::fwdDecl(const FwdDecl&)
{
  return 42;
}

int MyObject::const_parameters(const int input, QObject* const obj) const
{
  if (obj) return input / 3;
  return input / 2;
}

NonCopyable::NonCopyable()
  : mNum(new int(42))
{

}

NonCopyable::~NonCopyable()
{
  delete mNum;
}

namespace SomeNS {

NonCopyableInNS::NonCopyableInNS()
  : mNum(new int(42))
{

}

NonCopyableInNS::~NonCopyableInNS()
{
  delete mNum;
}

}

MyObject::MyIntegralMap MyObject::getMyMap() const
{
  MyIntegralMap m;
  m.insert(42, 7);
  return m;
}


MyObject::KeyBindingMap MyObject::getKeyBindings() const
{
  KeyBindingMap m;
  m.insert(TextCompletion, QString("CTRL+A"));
  return m;
}

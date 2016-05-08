
#pragma once

#include <QtCore/QObject>
#include <QtCore/QMap>

#include <functional>

class FwdDecl;

class MyObject : public QObject
{
  Q_OBJECT
public:
  MyObject(QObject* parent = nullptr);

  enum LocalEnum {
    Val1,
    Val2
  };
  Q_DECLARE_FLAGS(LocalEnums, LocalEnum)

  int addThree(int input) const;
  QList<int> addThree(QList<int> input) const;

  QString addThree(const QString& input, const QString& prefix = QStringLiteral("Default")) const;

  int findNeedle(QStringList list, QString needle, Qt::MatchFlags flags = Qt::MatchFlags(Qt::MatchStartsWith | Qt::MatchWrap)) const;

  int qtEnumTest(QFlags<Qt::MatchFlag> flags);
  int localEnumTest(QFlags<MyObject::LocalEnum> flags);

  int functionParam(std::function<int()> fn);
  int groups(unsigned int maxCount = std::numeric_limits<uint>::max()) const;

  int const_parameters(const int input, QObject* const obj = 0) const;

  int fwdDecl(const FwdDecl& f);
  int fwdDeclRef(FwdDecl& f);

  typedef QMap<int, int> MyIntegralMap;

  MyIntegralMap getMyMap() const;

    enum KeyBindingType {
      TextCompletion,
      PrevCompletionMatch,
      NextCompletionMatch,
      SubstringCompletion
  };
  typedef QMap<KeyBindingType, QString> KeyBindingMap;

  KeyBindingMap getKeyBindings() const;
};

class NonCopyable
{
public:
  NonCopyable();
  ~NonCopyable();

private:
  int* const mNum;
};

namespace SomeNS {

class NonCopyableInNS
{
public:
  NonCopyableInNS();
  ~NonCopyableInNS();

private:
  int* const mNum;
};

}

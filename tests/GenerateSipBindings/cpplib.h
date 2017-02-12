
#pragma once

#include <QtCore/QObject>
#include <QtCore/QString>
#include <QtCore/QStringList>
#include <QtCore/QMap>
#include <QtCore/QCoreApplication>
#include <QtCore/QSharedData>

#include <functional>

class ExternalFwdDecl;
class LocalFwdDecl;

template<typename T> class QList;

class MyObject : public QObject
{
  Q_OBJECT
public:
  MyObject(QObject* parent = nullptr);

  inline MyObject(const QString& inlineCtor, QObject* parent = nullptr);

  enum LocalEnum {
    Val1 = 1,
    Val2
  };
  Q_DECLARE_FLAGS(LocalEnums, LocalEnum)

  enum {
     AnonVal1,
     AnonVal2
  };

  double unnamedParameters(int, double);

  int addThree(int input) const;
  QList<int> addThree(QList<int> input) const;

  const QString addThree(const QString& input, const QString& prefix = QStringLiteral("Default")) const;

  int findNeedle(QStringList list, QString needle, Qt::MatchFlags flags = Qt::MatchFlags(Qt::MatchStartsWith | Qt::MatchWrap)) const;

  int qtEnumTest(QFlags<Qt::MatchFlag> flags);
  int localEnumTest(QFlags<MyObject::LocalEnum> flags);

  inline int inlineMethod(int arg);

  int functionParam(std::function<int()> fn);
  int groups(unsigned int maxCount = std::numeric_limits<uint>::max()) const;

  void enumNullptr(Qt::WindowFlags f = nullptr);

  void enumBraces(Qt::WindowFlags f = {});
  void stringBraces(QString s = {});
  void stringRefBraces(QString const& s = {});
  void intBraces(int i = {});
  void intRefBraces(int const& i = {});
  void pointerBraces(int* p = {});

  int const_parameters(const int input, QObject* const obj = 0) const;

  int externalFwdDecl(const ExternalFwdDecl& f);
  int externalFwdDeclRef(ExternalFwdDecl& f);

  int localFwdDecl(const LocalFwdDecl& f);

  int localListDecl(const QList<int>& l);

  int localDeclListDecl(const QList<LocalFwdDecl>& l);

  mode_t dummyFunc(QObject* parent) { return 0; }

signals:
  void publicSlotCalled();

Q_SIGNALS:
  void privateSlotCalled();
  void protectedSlotCalled();

public slots:
  void publicSlot1();

public Q_SLOTS:
  void publicSlot2();

protected slots:
  void protectedSlot1();

protected Q_SLOTS:
  void protectedSlot2();

private slots:
  void privateSlot1();

private Q_SLOTS:
  void privateSlot2();
};

inline MyObject::MyObject(const QString& inlineCtor, QObject* parent)
  : MyObject(parent)
{

}

inline int MyObject::inlineMethod(int arg)
{
  return arg;
}

class LocalFwdDecl
{
public:
  LocalFwdDecl(int value);

  int getValue() const;

private:
  int m_value;
};

class NonCopyable
{
public:
  NonCopyable();
  ~NonCopyable();

private:
  int* const mNum;
};

class NonCopyableByMacro
{
public:
  NonCopyableByMacro();

  Q_DECLARE_TR_FUNCTIONS(NonCopyableByMacro)

private:
  Q_DISABLE_COPY(NonCopyableByMacro)
};

Q_DECLARE_METATYPE(NonCopyableByMacro*)

class HasPrivateDefaultCtor
{
public:
private:
  HasPrivateDefaultCtor(int param = 0);
};

class Shared : public QSharedData
{
public:
  Shared(const Shared& other);
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

enum MyFlagType {
    EnumValueOne = 0x01,
    EnumValueTwo = 0x02
};
Q_DECLARE_FLAGS(MyFlags, MyFlagType)

qreal useEnum(MyFlags flags = EnumValueOne);

int customMethod(QList<int> const& nums);

typedef QString(*TagFormatter)(const QStringList &languages,
                               const QString &tagName,
                               const QHash<QString, QString> &attributes,
                               const QString &text,
                               const QStringList &tagPath,
                               SomeNS::MyFlagType format);

}

class TypedefUser
{
public:

  void setTagPattern(const QString &tagName,
                     SomeNS::TagFormatter formatter = NULL,
                     int leadingNewlines = 0);
};

int anotherCustomMethod(QList<int> const& nums);

enum __attribute__((visibility("default"))) EnumWithAttributes {
    Foo,
    Bar = 2
};

#define EXPORT __attribute__((visibility("default")))
#define NO_EXPORT __attribute__((visibility("hidden")))

class EXPORT Visible
{
public:
  EXPORT int visible_fn() { return 1; }
  NO_EXPORT int invisible_fn() { return 1; }
  EXPORT int visible;
  NO_EXPORT int invisible;
};

class NO_EXPORT Invisible
{
public:
  int someApi() { return 1; }
};

class Abstract
{
public:
  virtual ~Abstract();

  int callableMultiply(int i, int j);

protected:
  virtual void virtualInterface() = 0;
};

class Concrete : public Abstract
{
public:
  int callableAdd(int i, int j);

protected:
  void virtualInterface() override;
};

#define TEST_DEPRECATED __attribute__((__deprecated__))
class TEST_DEPRECATED DeprecatedClass
{
public:
  TEST_DEPRECATED void deprecatedFn(int bar) {};
};

class ObscureSyntax
{
public:
  /**
   * A friend declaration.
   */
  friend MyObject;

  enum LocalEnum {
    CORRECT = 555,
    INCORRECT
  };

  /**
   * Different types of default value, and a template parameter.
   * The function is *declared* to return INCORRECT, but we want to verify the %MethodCode returns CORRECT.
   */
  int defaultsAndParameterTemplate(
    //
    // Flags.
    //
    Qt::MatchFlags flagsOne = Qt::MatchWrap,
    Qt::MatchFlags flagsMultiple = Qt::MatchFlags(Qt::MatchStartsWith | Qt::MatchWrap),
    Qt::MatchFlags flagsMultipleSimple = Qt::MatchStartsWith | Qt::MatchWrap,
    //
    // Expressions.
    //
    int simple = 1,
    int complex = 1 + 1,
    int brackets = (1 + 1),
    //
    // Enum.
    //
    enum LocalEnum anEnum = INCORRECT,
    MyObject::LocalEnum remoteEnum = MyObject::Val2,
    //
    // Template. The template will need %MethodCode.
    //
    QMap<const char *, int> chachacha = QMap<const char *, int>(),
    //
    // Qualified object.
    //
    const SomeNS::NonCopyableInNS &qualified = SomeNS::NonCopyableInNS()) { return INCORRECT; }

  /**
   * A template return.
   * The function is *declared* to return an empty map, but we want to verify the %MethodCode returns CORRECT.
   */
  QMap<const char *, int> *returnTemplate() { return new QMap<const char *, int>(); }

  /**
   * Anonymous enum's need special logic to fixup clang's handling of them. See the code.
   */
  typedef LocalEnum TypedefForEnum;

  /**
   * Empty classes cannot be discarded.
   */
  class Empty
  {
  };

  /**
   * Test derivation from a templated class. This has two parts: stripping off the "class " part of the base class,
   * which is handled automatically, and the handling of base classes with a <>, currently left to the rules.
   *
   * The latter could be fixed up automatically by adding a synthetic typedef to the SIP as per
   * https://www.riverbankcomputing.com/pipermail/pyqt/2017-January/038660.html but the corresponding C++ typedef
   * can only be injected at global scope using the %TypeHeaderCode trick in the mailing list...that does not work
   * in the case of a nested class.
   */
  class TemplateDerivative : public QMap<int, int>
  {
  };

  /**
   * Typedef handling. See also LocalEnum and TemplateDerivative above.
   */
  typedef QMap<int, LocalEnum> TemplateTypedefWithIntegralTypes;
  typedef QMap<int, TemplateDerivative> TemplateTypedefWithNonIntegralTypes;
  struct anon_struct
  {
    int bar;
  };
  typedef struct anon_struct TypedefWithAnonymousStruct;
  typedef void *(*TypedefFnPtr)(char *a, int b);
  EXPORT typedef int TypdefVisible;
  NO_EXPORT int TypedefInvisible;
  typedef TemplateDerivative TypedefSimpleClass;
  class DerivativeViaTypedef : ObscureSyntax::TypedefSimpleClass
  {
  };
  //
  // This does not work for unknown reasons: "sip: .../cpplib.sip:279: Super-class list contains an invalid type".
  //
#if 0
  class TemplateDerivativeViaTypedef : ObscureSyntax::TemplateTypedefWithNonIntegralTypes
  {
  };
#endif

  /**
   * Verify %ModuleCode handling for:
   *
   *    - Type
   *    - Typedef (this also exercises the typedef rule database).
   *    - Function result
   *    - Function parameter
   */
  class ModuleCodeType : public QMap<int, int>
  {
  };
  typedef QMap<int, LocalEnum> ModuleCodeTypedef;
  QMap<int, TemplateDerivative> *moduleCodeFunction(QMap<int, TemplateDerivative> *parameter) { return NULL; };
  void moduleCodeParameter(QMap<int, TemplateDerivative> *parameter) { };
};

/**
 * Unexposed syntax.
 */
extern "C" double obscure_unexposed(const char *s00, char **se);

/**
 * Standalone static variable.
 */
static int standaloneStatic = 5;

class Variables
{
public:
  /**
   * In-class static variable.
   */
  static int classStatic;
  /**
   * Templated, in-class static variable.
   */
  static QMap<int, int> templatedClassStatic;
  /**
   * Templated variable. TODO: this does not work because SIP seems to omit the sipPySelf argument name.
   */
  // QMap<int, int> templatedVar;
};

/**
 * extern support.
 */
extern const char externVar;

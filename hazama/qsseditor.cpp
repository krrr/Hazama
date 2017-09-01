#include "qsseditor.h"
#include "globals.h"
#include <QSyntaxHighlighter>
#include <QPushButton>
#include <QTextEdit>
#include <QRegularExpression>
#include <QVBoxLayout>
#include <QDialogButtonBox>
#include <QAbstractButton>


class QSSHighlighter : public QSyntaxHighlighter {
    static constexpr const char* pattern = "((?:\\.|#)?[_a-zA-Z][a-zA-Z0-9_-]*)|"  // ID
    "(#[0-9a-fA-F]{3,6}|\\d+(?:\\.\\d+)?(?:pt|px|em|dip)?)|"  // DIGIT
    "(/\\*)|"  // COMM_START
    "(\\*/)|"  // COMM_END
    "({)|"  // BLOCK_START
    "(})|"  // BLOCK_END
    "(\\[[^\\]]*\\]|\\s+|.)";  // SKIP; skip property selector
    // id may conflict with digit

    enum class State { NORMAL, IN_BLOCK, IN_COMMENT, IN_BLOCK_COMMENT };
    enum class Group { __, ID, DIGIT, COMM_START, COMM_END, BLOCK_START, BLOCK_END, SKIP };

    QTextCharFormat commentFmt, selectorFmt, propertyFmt, digitFmt, defaultFmt;
    QRegularExpression re;

    State myCurBlockState() { return static_cast<State>(currentBlockState()); }
    void mySetCurBlockState(State i) { setCurrentBlockState(int(i)); }

public:
    QSSHighlighter(QTextDocument *parent=nullptr) : QSyntaxHighlighter(parent) {
        commentFmt.setForeground(Qt::darkGray);
        selectorFmt.setForeground(QColor("#0e3c76"));
        propertyFmt.setForeground(QColor("#4370a7"));
        digitFmt.setForeground(QColor("#d02424"));
        re.setPattern(pattern);
        re.setPatternOptions(QRegularExpression::MultilineOption);
    }

    void highlightBlock(const QString &text) {
        int	p = previousBlockState();
        setCurrentBlockState((p == -1) ? int(State::NORMAL) : p);
        int commStart = 0;
        int offset = 0;
        QRegularExpressionMatch prevMatch;
        Group prevGroup;

        while (offset < text.length()) {
            auto match = re.match(text, offset);
            Group group = Group::__;
            for (int i : range(1, match.lastCapturedIndex()+1))
                if (!match.captured(i).isNull()) {
                    group = static_cast<Group>(i);
                    break;
                }
            Q_ASSERT(group != Group::__);

            if (myCurBlockState() == State::NORMAL) {
                if (group == Group::ID)
                    setFormat(match.capturedStart(), match.capturedLength(), selectorFmt);
                else if(group == Group::COMM_START) {
                    commStart = match.capturedStart();
                    mySetCurBlockState(State::IN_COMMENT);
                } else if(group == Group::BLOCK_START)
                    mySetCurBlockState(State::IN_BLOCK);
            } else if (myCurBlockState() == State::IN_COMMENT || myCurBlockState() == State::IN_BLOCK_COMMENT) {
                if (group == Group::COMM_END) {
                    setFormat(commStart, match.capturedEnd()-commStart, commentFmt);
                    if (myCurBlockState() == State::IN_BLOCK_COMMENT)
                        mySetCurBlockState(State::IN_BLOCK);
                    else
                        mySetCurBlockState(State::NORMAL);
                }
            } else if (myCurBlockState() == State::IN_BLOCK) {
                if (group == Group::BLOCK_END)
                    mySetCurBlockState(State::NORMAL);
                else if (group == Group::COMM_START) {
                    commStart = match.capturedStart();
                    mySetCurBlockState(State::IN_BLOCK_COMMENT);
                } else if (group == Group::ID || group == Group::DIGIT)
                    setFormat(match.capturedStart(), match.capturedLength(), digitFmt);

                if (match.captured() == ":" && prevGroup == Group::ID )
                    setFormat(prevMatch.capturedStart(), prevMatch.capturedLength(), propertyFmt);
            }
            prevMatch = match;
            prevGroup = group;
            offset += match.capturedLength();
        }

        if (myCurBlockState() == State::IN_COMMENT)
            setFormat(commStart, text.length()-commStart, commentFmt);
    }
};


QssEditor::QssEditor(QWidget *parent) : QDialog(parent) {
    setWindowFlags(Qt::Window | Qt::WindowCloseButtonHint);
    setAttribute(Qt::WA_DeleteOnClose);

    setWindowTitle("Style Sheet Editor");

    buttonBox = new QDialogButtonBox(this);
    applyBtn = buttonBox->addButton("Preview", QDialogButtonBox::ApplyRole);
    saveBtn = buttonBox->addButton("Save", QDialogButtonBox::AcceptRole);
    cancelBtn = buttonBox->addButton("Cancel", QDialogButtonBox::RejectRole);
    connect(buttonBox, &QDialogButtonBox::clicked, this, &QssEditor::onButtonClicked);

    edit = new QTextEdit(this);
    edit->setFont(QFont((osInfo.isWin) ? "Consolas" : "monospace"));
    edit->setStyleSheet("QPlainTextEdit { border: none; }");
    new QSSHighlighter(edit->document());
    edit->setPlainText(qApp->property("originStyleSheet").toString());
    edit->find(CUSTOM_STYLESHEET_DELIMIT);
    edit->moveCursor(QTextCursor::End);
    edit->setFocus();

    auto layout = new QVBoxLayout(this);
    int m = 7 * scaleRatio;
    layout->setContentsMargins(m, m, m, m);
    layout->addWidget(edit);
    layout->addWidget(edit);
    layout->addWidget(buttonBox);
}


void QssEditor::onButtonClicked(QAbstractButton *btn) {
    if (static_cast<QPushButton*>(btn) == cancelBtn) {
        close();
        return;
    }

    setStyleSheetPatched(edit->toPlainText());

    if (static_cast<QPushButton*>(btn) == saveBtn) {
        auto ss = edit->toPlainText().section(CUSTOM_STYLESHEET_DELIMIT, 1).trimmed();
        QFile f(dataDir + "/custom.qss");
        f.open(QIODevice::WriteOnly | QIODevice::Text);
        f.write(ss.toUtf8());
        close();
    }
}

#pragma once
#include <functional>


template<class Derived, class TrueBase>
class FormatterMixin : public TrueBase {
public:
    QColor highLightColor = QColor(248, 162, 109, 100);

    using TrueBase::TrueBase;

    // Apply XX format to current selection if true, otherwise clear that format
    void setHighLight(bool apply) { doFormat(apply,
            [&](auto *fmt){ fmt->setBackground(QBrush(highLightColor)); },
            [](auto *fmt){ fmt->clearProperty(QTextFormat::BackgroundBrush); });
    }
    void setBold(bool apply) { doFormat(apply,
            [](auto *fmt){ fmt->setFontWeight(QFont::Bold); },
            [](auto *fmt){ fmt->clearProperty(QTextFormat::FontWeight); });
    }
    void setStrikeOut(bool apply) { doFormat(apply,
            [](auto *fmt){ fmt->setFontStrikeOut(true); },
            [](auto *fmt){ fmt->clearProperty(QTextFormat::FontStrikeOut); });
    }
    void setUnderline(bool apply) { doFormat(apply,
            [](auto *fmt){ fmt->setFontUnderline(true); },
            [](auto *fmt){ fmt->clearProperty(QTextFormat::TextUnderlineStyle); });
    }
    void setItalic(bool apply) { doFormat(apply,
            [](auto *fmt){ fmt->setFontItalic(true); },
            [](auto *fmt){ fmt->clearProperty(QTextFormat::FontItalic); });
    }

private:
    // derived should have textCursor()
    using ActFunc = std::function<void(QTextCharFormat*)>;
    inline void doFormat(bool apply, ActFunc applyFunc, ActFunc clearFunc) {
        auto cur = static_cast<Derived*>(this)->textCursor();
        auto fmt = cur.charFormat();
        if (apply) {
            applyFunc(&fmt);
            cur.mergeCharFormat(fmt);
        } else {
            clearFunc(&fmt);
            cur.setCharFormat(fmt);
        }
    }
};

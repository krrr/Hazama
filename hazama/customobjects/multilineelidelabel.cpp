#include <QTextLayout>
#include <QPainter>
#include "globals.h"
#include "multilineelidelabel.h"

MultiLineElideLabel::MultiLineElideLabel(QWidget *parent, bool forceHeightHint) :
	QFrame(parent), forceHeightHint(forceHeightHint) {
	layout.setCacheEnabled(true);
	updateSize();
}

void MultiLineElideLabel::setText(QString text) {
	text.replace('\n', QChar(0x2028));
	this->text = text;
}

void MultiLineElideLabel::resizeEvent(QResizeEvent *event) {
	setupLayout();
	QFrame::resizeEvent(event);
}

void MultiLineElideLabel::setFont(const QFont &f) {
	QFrame::setFont(f);
	updateSize();
	setupLayout();
}

QSize MultiLineElideLabel::sizeHint() const {
	auto m = contentsMargins();
	return QSize(-1, realHeight+m.top()+m.bottom());
}

void MultiLineElideLabel::paintEvent(QPaintEvent *) {
	QPainter p(this);
	p.translate(contentsRect().topLeft());
	layout.draw(&p, QPoint());
	if (!elideMarkPos.isNull())
		p.drawText(elideMarkPos, elideMark);
}

void MultiLineElideLabel::updateSize() {
	// use height because leading is not included
	// this make realHeight equals heightHint even if font fallback happen
	lineHeight = fontMetrics().height();
	heightHint = lineHeight * maximumLineCount;
	elideMarkWidth = fontMetrics().width(elideMark);
	if (forceHeightHint)
		realHeight = heightHint;
}

void MultiLineElideLabel::setupLayout() {
	layout.clearLayout();
	layout.setFont(font());

	if (text.isEmpty() || maximumLineCount == 0) {
		if (realHeight != 0 && !forceHeightHint) {
			updateGeometry();
			realHeight = 0;
		}
		return;
	}

	int lineWidthLimit = contentsRect().width();
	layout.setText(text);
	int height = 0;
	int visibleTextLen = 0;
	int linesLeft = maximumLineCount;
	elideMarkPos = QPoint(0, 0);  // null point

	layout.beginLayout();
	while (true) {
		auto line = layout.createLine();
		if (!line.isValid())
			break;  // call meths of invalid one will segfaulodt

		line.setLineWidth(lineWidthLimit);
		visibleTextLen += line.textLength();
		line.setPosition(QPointF(0, height));
		height += line.height();

		linesLeft -= 1;
		if (linesLeft == 0) {
			if (visibleTextLen < text.length()) {
				// ignore right to left text
				line.setLineWidth(lineWidthLimit - elideMarkWidth);
				elideMarkPos = QPoint(line.naturalTextWidth(),
									  height-line.height()+fontMetrics().ascent());
			}
			break;
		}
	}
	layout.endLayout();
	if (height != realHeight && !forceHeightHint) {
		updateGeometry();
		realHeight = height;
	}
}

void MultiLineElideLabel::setMaximumLineCount(int lines) {
	// 0 means unlimited
	if (lines == maximumLineCount)
		return;
	maximumLineCount = lines;
	setupLayout();
	updateSize();
}

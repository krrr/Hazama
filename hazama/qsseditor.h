#pragma once
#include <QDialog>

class QDialogButtonBox;
class QPushButton;
class QAbstractButton;
class QTextEdit;


class QssEditor : public QDialog {
public:
	QssEditor(QWidget *parent=nullptr);

private:
	QDialogButtonBox *buttonBox;
	QPushButton *applyBtn, *cancelBtn, *saveBtn;
	QTextEdit *edit;

	void onButtonClicked(QAbstractButton *btn);
};
